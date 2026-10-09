"""Independent versioned onboarding contracts and semantic destination rules."""
import hashlib
import json
import re
import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .contracts import Contract, Binding, Descriptor, ID
from .configuration import ConfigError, pairs, reject_secrets, safe_path

SHA = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def destination_path(value):
    if not value or '\\' in value or value.startswith('/'):
        raise ConfigError('invalid_destination')
    for part in value.split('/'):
        if (part in ('', '.', '..') or part.endswith(('.', ' ')) or
            re.search(r'[<>:"|?*\x00-\x1f]', part) or
            re.fullmatch(r'(?i)(con|prn|aux|nul|com[0-9¹²³]|lpt[0-9¹²³])(?:\..*)?', part)):
            raise ConfigError('invalid_destination')
    return value


def absolute_path(value):
    p = Path(value)
    if not p.is_absolute() or str(p).startswith(('\\\\', '//')):
        raise ConfigError('invalid_destination')
    for part in p.parts[1:]:
        destination_path(part)
    return safe_path(p)


def separate(paths):
    resolved = [absolute_path(p) for p in paths]
    for i, a in enumerate(resolved):
        for b in resolved[i + 1:]:
            if a == b or a.is_relative_to(b) or b.is_relative_to(a):
                raise ConfigError('overlapping_paths')


def unmanaged_path(path):
    path = absolute_path(str(path))
    roots = [Path.home() / '.codex', Path.home() / '.config/openspec']
    for key in ('CODEX_HOME', 'XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'APPDATA', 'LOCALAPPDATA'):
        if os.environ.get(key):
            roots.append(Path(os.environ[key]) / ('openspec' if key != 'CODEX_HOME' else ''))
    if any(path == root or path.is_relative_to(root) or root.is_relative_to(path) for root in roots):
        raise ConfigError('managed_path')
    return path


class Operation(Contract):
    kind: Literal['create_file'] = 'create_file'
    scope: Literal['target', 'binding']
    path: str
    content: Annotated[str, Field(max_length=128 * 1024)]
    sha256: SHA

    @model_validator(mode='after')
    def valid(self):
        data = self.content.encode('utf-8')
        if len(data) > 128 * 1024 or sha(data) != self.sha256:
            raise ValueError('invalid payload')
        if self.scope == 'target':
            destination_path(self.path)
        else:
            absolute_path(self.path)
        return self


class OnboardingPlan(Contract):
    kind: Literal['onboarding_plan'] = 'onboarding_plan'
    kit_version: Literal['0.1.0'] = '0.1.0'
    resource_manifest_sha256: SHA
    target_path: str
    origin: str
    policy_path: str
    policy_sha256: SHA
    binding_path: str
    binding_mode: Literal['existing', 'proposed']
    binding: Binding
    descriptor: Descriptor
    input_hashes: dict[str, SHA]
    absent_paths: list[str]
    applicable: bool
    operations: Annotated[list[Operation], Field(max_length=64)]
    plan_sha256: SHA

    @model_validator(mode='after')
    def valid(self):
        separate([self.target_path, self.policy_path, self.binding_path, self.binding.state_dir])
        unmanaged_path(self.binding_path)
        unmanaged_path(self.binding.state_dir)
        paths = [(o.scope, o.path.lower()) for o in self.operations]
        if len(paths) != len(set(paths)) or len(self.absent_paths) != len(set(p.lower() for p in self.absent_paths)):
            raise ValueError('duplicate destinations')
        for path in self.absent_paths:
            destination_path(path)
        data = self.model_dump(exclude={'plan_sha256'})
        if sha(canonical(data)) != self.plan_sha256 or len(canonical(self.model_dump())) > 1024 * 1024:
            raise ValueError('invalid integrity')
        return self


class JournalOperation(Contract):
    scope: Literal['target', 'binding', 'state']
    kind: Literal['file', 'directory']
    path: str
    state: Literal['planned', 'creating', 'created', 'failed', 'removed', 'conflict']
    sha256: SHA | None = None
    file_identity: str | None = None


class Journal(Contract):
    kind: Literal['onboarding_journal'] = 'onboarding_journal'
    client_id: ID
    checkout_id: ID
    run_id: ID
    plan_sha256: SHA
    target_path: str
    binding_path: str
    policy_sha256: SHA
    state: Literal['in_progress', 'completed', 'failed', 'recovered', 'recovery_conflict']
    operations: Annotated[list[JournalOperation], Field(max_length=256)]


def load_json(path, model, limit=1024 * 1024):
    path = safe_path(path)
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ConfigError('document_too_large')
    try:
        data = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs)
        reject_secrets(data)
        return model.model_validate(data)
    except ConfigError:
        raise
    except (ValueError, TypeError, RecursionError):
        raise ConfigError('invalid_plan' if model is OnboardingPlan else 'invalid_journal') from None


def load_plan(path):
    return load_json(path, OnboardingPlan)


def denied(path, patterns):
    path_parts = path.lower().split('/')
    for pattern in patterns:
        parts = pattern.lower().rstrip('/').split('/')
        @lru_cache(None)
        def matches(i, j):
            if i == len(parts):
                return True  # Protect all descendants of a matched ancestor.
            if parts[i] == '**':
                return matches(i + 1, j) or (j < len(path_parts) and matches(i, j + 1))
            regex = ''.join('[^/]*' if x == '*' else '[^/]' if x == '?' else re.escape(x) for x in parts[i])
            return j < len(path_parts) and bool(re.fullmatch(regex, path_parts[j])) and matches(i + 1, j + 1)
        if matches(0, 0):
            return True
    return False


def authorize(operations, policy):
    target = [o for o in operations if o.scope == 'target']
    if len(target) > policy.max_files or sum(len(o.content.encode('utf-8')) for o in target) > policy.max_bytes:
        return 'policy_limit'
    if any(denied(o.path, policy.read_only_paths + policy.denied_paths) for o in target):
        return 'policy_denied'
    return None
