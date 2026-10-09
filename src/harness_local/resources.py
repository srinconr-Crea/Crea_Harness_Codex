"""Pinned, offline OpenSpec resources; integrity is checked before planning."""
import hashlib
import json
from importlib.resources import files

from harness_core.configuration import ConfigError, pairs
from .diagnostics import SKILLS


def kit(root=None):
    root = root or files('harness_local').joinpath('openspec_kit')
    try:
        raw = root.joinpath('manifest.json').read_bytes()
        manifest = json.loads(raw, object_pairs_hook=pairs)
        expected = {'openspec/config.yaml', *[f'.agents/skills/{name}/SKILL.md' for name in SKILLS], 'LICENSE'}
        if manifest['version'] != '1.13.2' or set(manifest['files']) != expected:
            raise ValueError()
        result = {}
        for path, sha in manifest['files'].items():
            content = root.joinpath(path).read_bytes()
            if len(content) > 128 * 1024 or hashlib.sha256(content).hexdigest() != sha:
                raise ValueError()
            if path != 'LICENSE':
                result[path] = content.decode('utf-8')
        return result, hashlib.sha256(raw).hexdigest()
    except (OSError, ValueError, KeyError, TypeError):
        raise ConfigError('kit_resources_invalid') from None
