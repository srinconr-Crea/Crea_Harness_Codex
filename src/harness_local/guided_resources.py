"""Passive onboarding resources with a release dependency receipt."""
import json
from importlib.resources import files

from harness_core.configuration import ConfigError, pairs
from harness_core.onboarding_plan import canonical, sha, destination_path


def resources():
    root = files('harness_local').joinpath('guided_kit')
    try:
        manifest = json.loads(root.joinpath('manifest.json').read_bytes(), object_pairs_hook=pairs)
        if set(manifest) != {'schema_version', 'files'} or manifest['schema_version'] != 1: raise ValueError()
        result = {}
        for name, expected in manifest['files'].items():
            destination_path(name)
            raw = root.joinpath(name).read_bytes()
            if len(raw) > 128 * 1024 or sha(raw) != expected: raise ValueError()
            result[name] = raw.decode('utf-8')
        receipt = json.loads(result['dependency.json'])
        if receipt['change'] != '02-desktop-roles-and-tool-contracts' or receipt['status'] != 'verified-supervised' or not receipt['implementation_commit'] or not receipt['evidence']:
            raise ConfigError('guided_dependency_pending')
        return result
    except (ValueError, KeyError, TypeError, OSError, UnicodeError):
        raise ConfigError('guided_resources_invalid') from None


def resource_digest(): return sha(canonical(resources()))
