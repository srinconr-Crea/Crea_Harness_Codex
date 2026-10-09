"""External JSON evidence and an explicit checkout lock with process identity."""
import ctypes as c
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import uuid

from pydantic import Field

from harness_core.contracts import Contract, ID
from harness_core.configuration import ConfigError, safe_path
from harness_core.onboarding_plan import canonical, load_json, absolute_path
from .windows_fs import PinnedTree


class LockOwner(Contract):
    pid: int = Field(gt=0)
    started: str = Field(pattern=r'^[0-9]+$')
    run_id: ID


def process_identity(pid):
    """None proves the PID absent; access-denied is an unknown/live owner."""
    kernel = c.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    kernel.OpenProcess.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.GetProcessTimes.argtypes = [w.HANDLE, *[c.POINTER(w.FILETIME)] * 4]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        if c.get_last_error() == 87:
            return None
        raise ConfigError('lock_owner_unknown')
    try:
        times = [w.FILETIME() for _ in range(4)]
        if not kernel.GetProcessTimes(handle, *[c.byref(x) for x in times]):
            raise ConfigError('lock_owner_unknown')
        # A terminated process whose kernel object is still retained is dead.
        if times[1].dwHighDateTime or times[1].dwLowDateTime:
            return None
        return str((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime)
    finally:
        kernel.CloseHandle(handle)


def ensure_state(binding):
    state = absolute_path(binding.state_dir)
    ancestor = state
    while not ancestor.exists():
        ancestor = ancestor.parent
    if not ancestor.is_dir():
        raise ConfigError('state_path_invalid')
    with PinnedTree(ancestor) as tree:
        parts = state.relative_to(ancestor).parts
        for i in range(1, len(parts) + 1):
            relative = '/'.join(parts[:i])
            try:
                with tree.directory(relative, create=True):
                    pass
            except ConfigError as error:
                if error.code != 'destination_exists':
                    raise
                with tree.directory(relative):
                    pass
    return state


def persist(path, journal):
    """Atomic journal replacement; its parent remains pinned through replacement."""
    path = safe_path(path)
    data = canonical(journal.model_dump()) + b'\n'
    if len(data) > 1024 * 1024:
        raise ConfigError('journal_too_large')
    with PinnedTree(path.parent) as tree:
        temporary = 'journal-' + uuid.uuid4().hex + '.tmp'
        with tree.file(temporary, create=True) as handle:
            handle.write(data)
        # os.replace replaces a leaf link rather than following it. Parent
        # components cannot be swapped while their no-delete handles remain.
        os.replace(path.parent / temporary, path)


class CheckoutLock:
    def __init__(self, state, run_id, recover=False):
        self.state = safe_path(state)
        self.run_id = run_id
        self.recover = recover
        self.pid = os.getpid()
        self.started = process_identity(self.pid)
        self.tree = None

    def __enter__(self):
        self.tree = PinnedTree(self.state)
        try:
            if self.recover and (self.state / 'onboarding.lock').exists():
                # Read and delete the exact same exclusive handle, preventing
                # an owner swap between the liveness check and lock removal.
                with self.tree.file('onboarding.lock', delete=True) as handle:
                    from harness_core.configuration import pairs
                    try:
                        owner = LockOwner.model_validate(json.loads(handle.read(4096), object_pairs_hook=pairs))
                    except (ValueError, TypeError):
                        raise ConfigError('invalid_lock') from None
                    observed = process_identity(owner.pid)
                    if observed == owner.started:
                        raise ConfigError('onboarding_locked')
                    handle.delete()
            owner = LockOwner(schema_version=1, pid=self.pid, started=self.started, run_id=self.run_id)
            with self.tree.file('onboarding.lock', create=True) as handle:
                handle.write(canonical(owner.model_dump()))
                self.identity = handle.identity()
            return self
        except ConfigError as error:
            self.tree.__exit__()
            self.tree = None
            if error.code == 'destination_exists':
                raise ConfigError('onboarding_locked') from None
            raise

    def __exit__(self, *args):
        if self.tree:
            try:
                with self.tree.file('onboarding.lock', delete=True) as handle:
                    if handle.identity() != self.identity:
                        raise ConfigError('lock_changed')
                    handle.delete()
            finally:
                self.tree.__exit__()
                self.tree = None
