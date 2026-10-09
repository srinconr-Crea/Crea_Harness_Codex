import os
import subprocess

import pytest

from harness_core.configuration import ConfigError


def test_exclusive_pinned_creation(scratch):
    from harness_local.windows_fs import PinnedTree
    with PinnedTree(scratch) as tree:
        with tree.file('hello.txt', create=True) as handle:
            handle.write(b'hello')
            identity = handle.identity()
        assert (scratch / 'hello.txt').read_bytes() == b'hello'
        with pytest.raises(ConfigError):
            with tree.file('hello.txt', create=True):
                pass
        with tree.file('hello.txt') as handle:
            assert handle.identity() == identity
            assert handle.read() == b'hello'
            with pytest.raises(OSError):
                (scratch / 'hello.txt').write_bytes(b'overwrite')


def test_ancestor_rename_and_junction_rejected(scratch):
    from harness_local.windows_fs import PinnedTree
    parent = scratch / 'parent'
    parent.mkdir()
    outside = scratch / 'outside'
    outside.mkdir()
    with PinnedTree(parent):
        with pytest.raises(OSError):
            parent.rename(scratch / 'moved')
    junction = parent / 'link'
    result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(junction), str(outside)], capture_output=True)
    assert result.returncode == 0
    with PinnedTree(parent) as tree:
        with pytest.raises(ConfigError):
            with tree.file('link/escape.txt', create=True):
                pass
    assert not (outside / 'escape.txt').exists()
