"""Windows handle-relative, no-reparse, exclusive creation.

Directory handles omit FILE_SHARE_DELETE for their entire lifetime. Each next
component is opened relative to the pinned parent with NtCreateFile; client
paths are never reopened by an absolute string after validation.
"""
import ctypes as c
from ctypes import wintypes as w
from contextlib import contextmanager
import os
from pathlib import Path

from harness_core.configuration import ConfigError, safe_path


class UnicodeString(c.Structure):
    _fields_ = [('Length', w.USHORT), ('MaximumLength', w.USHORT), ('Buffer', w.LPWSTR)]


class ObjectAttributes(c.Structure):
    _fields_ = [('Length', w.ULONG), ('RootDirectory', w.HANDLE), ('ObjectName', c.POINTER(UnicodeString)),
                ('Attributes', w.ULONG), ('SecurityDescriptor', c.c_void_p), ('SecurityQualityOfService', c.c_void_p)]


class IOStatus(c.Structure):
    _fields_ = [('Status', c.c_void_p), ('Information', c.c_size_t)]


class FileInfo(c.Structure):
    _fields_ = [('attributes', w.DWORD), ('creation', w.FILETIME), ('access', w.FILETIME),
                ('write', w.FILETIME), ('volume', w.DWORD), ('size_high', w.DWORD), ('size_low', w.DWORD),
                ('links', w.DWORD), ('index_high', w.DWORD), ('index_low', w.DWORD)]


def api():
    if os.name != 'nt':
        raise ConfigError('confinement_unavailable')
    kernel = c.WinDLL('kernel32', use_last_error=True)
    nt = c.WinDLL('ntdll')
    kernel.CreateFileW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, c.c_void_p, w.DWORD, w.DWORD, w.HANDLE]
    kernel.CreateFileW.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.GetFileInformationByHandle.argtypes = [w.HANDLE, c.POINTER(FileInfo)]
    kernel.ReadFile.argtypes = [w.HANDLE, c.c_void_p, w.DWORD, c.POINTER(w.DWORD), c.c_void_p]
    kernel.WriteFile.argtypes = kernel.ReadFile.argtypes
    kernel.FlushFileBuffers.argtypes = [w.HANDLE]
    kernel.SetFilePointerEx.argtypes = [w.HANDLE, c.c_longlong, c.c_void_p, w.DWORD]
    kernel.SetEndOfFile.argtypes = [w.HANDLE]
    kernel.SetFileInformationByHandle.argtypes = [w.HANDLE, c.c_int, c.c_void_p, w.DWORD]
    kernel.GetFinalPathNameByHandleW.argtypes = [w.HANDLE, w.LPWSTR, w.DWORD, w.DWORD]
    nt.NtCreateFile.argtypes = [c.POINTER(w.HANDLE), w.DWORD, c.POINTER(ObjectAttributes),
                              c.POINTER(IOStatus), c.c_void_p, w.ULONG, w.ULONG,
                              w.ULONG, w.ULONG, c.c_void_p, w.ULONG]
    nt.NtCreateFile.restype = c.c_int32
    return kernel, nt


class Handle:
    def __init__(self, raw, kernel):
        self.raw, self.kernel = raw, kernel
        self.info = FileInfo()
        if not kernel.GetFileInformationByHandle(raw, c.byref(self.info)) or self.info.attributes & 0x400:
            self.close()
            raise ConfigError('linked_path')
        if self.info.links > 1:
            self.close()
            raise ConfigError('linked_path')

    def identity(self):
        return f'{self.info.volume:x}:{self.info.index_high:x}:{self.info.index_low:x}:{self.info.creation.dwHighDateTime:x}:{self.info.creation.dwLowDateTime:x}'

    def final_path(self):
        buffer = c.create_unicode_buffer(32768)
        length = self.kernel.GetFinalPathNameByHandleW(self.raw, buffer, len(buffer), 0)
        if not length or length >= len(buffer) or not buffer.value.startswith('\\\\?\\'):
            raise ConfigError('confinement_unavailable')
        return Path(buffer.value[4:])

    def close(self):
        if self.raw is not None:
            self.kernel.CloseHandle(self.raw)
            self.raw = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def write(self, data):
        count = w.DWORD()
        if not self.kernel.WriteFile(self.raw, data, len(data), c.byref(count), None) or count.value != len(data):
            raise ConfigError('write_failed')
        if not self.kernel.FlushFileBuffers(self.raw):
            raise ConfigError('flush_failed')

    def read(self, limit=1024 * 1024):
        buffer = c.create_string_buffer(limit + 1)
        count = w.DWORD()
        if not self.kernel.ReadFile(self.raw, buffer, limit + 1, c.byref(count), None):
            raise ConfigError('read_failed')
        if count.value > limit:
            raise ConfigError('document_too_large')
        return buffer.raw[:count.value]

    def delete(self):
        flag = w.BOOL(1)
        if not self.kernel.SetFileInformationByHandle(self.raw, 4, c.byref(flag), c.sizeof(flag)):
            raise ConfigError('delete_failed')

    def replace_bytes(self, data):
        """Edit the same exclusive file object after an external backup is durable.

        This is not an atomic transaction. Interrupted writes are detected by
        the integration journal and require explicit conservative recovery.
        """
        if not self.kernel.SetFilePointerEx(self.raw, 0, None, 0):
            raise ConfigError('write_failed')
        self.write(data)
        if not self.kernel.SetEndOfFile(self.raw):
            raise ConfigError('write_failed')
        if not self.kernel.FlushFileBuffers(self.raw):
            raise ConfigError('flush_failed')


class PinnedTree:
    def __init__(self, root):
        self.kernel, self.nt = api()
        self.root = safe_path(root)
        if not self.root.is_dir():
            raise ConfigError('parent_missing')
        self.handles = []
        try:
            raw = self.kernel.CreateFileW(str(self.root.anchor), 0x100081, 3, None, 3, 0x02200000, None)
            if raw == c.c_void_p(-1).value:
                raise ConfigError('confinement_unavailable')
            current = Handle(raw, self.kernel)
            self.handles.append(current)
            for part in self.root.parts[1:]:
                current = self._open(current, part, directory=True)
                self.handles.append(current)
            self.base = current
            if self.base.final_path() != self.root:
                raise ConfigError('destination_alias')
        except BaseException:
            self.__exit__()
            raise

    def _open(self, parent, name, directory=False, create=False, delete=False, editable=False):
        from harness_core.onboarding_plan import destination_path
        destination_path(name)
        text = c.create_unicode_buffer(name)
        length = len(name.encode('utf-16-le'))
        unicode = UnicodeString(length, length + 2, c.cast(text, w.LPWSTR))
        attrs = ObjectAttributes(c.sizeof(ObjectAttributes), parent.raw, c.pointer(unicode), 0x40, None, None)
        status = IOStatus()
        raw = w.HANDLE()
        access = 0x100081 if directory else (0x40100081 if create else 0x100081)
        if delete:
            access |= 0x10000
        if editable:
            access |= 0x40000000
        options = 0x00200000 | 0x20 | (1 if directory else 0x40)
        result = self.nt.NtCreateFile(c.byref(raw), access, c.byref(attrs), c.byref(status), None,
                                     0, 3 if directory else 1, 2 if create else 1, options, None, 0)
        if result < 0:
            if result & 0xffffffff == 0xc0000035:
                raise ConfigError('destination_exists')
            raise ConfigError('confinement_rejected')
        handle = Handle(raw.value, self.kernel)
        try:
            if handle.final_path() != parent.final_path() / name:
                raise ConfigError('destination_alias')
            return handle
        except BaseException:
            handle.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *args):
        for handle in reversed(self.handles):
            handle.close()
        self.handles.clear()

    @contextmanager
    def file(self, relative, create=False, delete=False):
        with self.entry(relative,create=create,delete=delete) as handle:
            yield handle

    @contextmanager
    def directory(self, relative, create=False, delete=False):
        with self.entry(relative,directory=True,create=create,delete=delete) as handle:
            yield handle

    @contextmanager
    def editable_file(self, relative, delete=False):
        with self.entry(relative, editable=True, delete=delete) as handle:
            yield handle

    @contextmanager
    def entry(self, relative, directory=False, create=False, delete=False, editable=False):
        from harness_core.onboarding_plan import destination_path
        destination_path(relative)
        current = self.base
        parts = relative.split('/')
        with_handles = []
        try:
            for name in parts[:-1]:
                current = self._open(current, name, directory=True)
                with_handles.append(current)
            with self._open(current, parts[-1], directory=directory, create=create, delete=delete, editable=editable) as handle:
                yield handle
        finally:
            for handle in reversed(with_handles):
                handle.close()
