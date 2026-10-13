"""Reviewed passive templates. Loading never installs or executes a runner."""
import json
from importlib.resources import files
from harness_core.configuration import ConfigError
from harness_core.onboarding_plan import sha,destination_path


def resources():
    root=files('harness_local').joinpath('validation_kit')
    manifest=json.loads(root.joinpath('manifest.json').read_bytes())
    if manifest.get('schema_version')!=1: raise ConfigError('validation_resource_integrity')
    result={}
    for entry in manifest['files']:
        destination_path(entry['path'])
        raw=root.joinpath(entry['path']).read_bytes()
        if sha(raw)!=entry['sha256'] or len(raw)!=entry['bytes']: raise ConfigError('validation_resource_integrity')
        result[entry['path']]=raw
    return result
