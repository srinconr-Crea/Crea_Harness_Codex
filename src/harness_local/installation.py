"""Validate the offline installation closure before any binary is executed."""
import json
from pathlib import Path
import zipfile
from importlib.resources import files

from harness_core.configuration import ConfigError, pairs, safe_path
from harness_core.onboarding_plan import destination_path, sha


def validate_kit(path):
    root=safe_path(path)
    try:
        manifest=json.loads((root/'install-manifest.json').read_bytes(),object_pairs_hook=pairs)
        if set(manifest)!={'schema_version','version','platform','files','tools','runtime_dependencies','wheel','skill'}:
            raise ValueError()
        if manifest['schema_version']!=1 or manifest['platform']!='windows-amd64' or manifest['version']!='0.1.0': raise ValueError()
        for name,expected in manifest['files'].items():
            destination_path(name)
            if sha(safe_path(root/name).read_bytes())!=expected: raise ValueError()
        names=set()
        for dep in manifest['runtime_dependencies']:
            if set(dep)!={'name','version','artifact','sha256','license'}: raise ValueError()
            if not dep['license'] or manifest['files'].get('wheelhouse/'+dep['artifact'])!=dep['sha256']: raise ValueError()
            with zipfile.ZipFile(root/'wheelhouse'/dep['artifact']) as wheel:
                info=wheel.read(next(n for n in wheel.namelist() if n.endswith('.dist-info/METADATA'))).decode()
            headers=info.split('\n\n',1)[0].splitlines()
            if 'Version: '+dep['version'] not in headers: raise ValueError()
            names.add(dep['name'].lower().replace('_','-'))
        # These are the complete selected cp313 runtime closure, not dev extras.
        if names!={'pydantic','pydantic-core','pyyaml','annotated-types','typing-extensions','typing-inspection'}: raise ValueError()
        if set(manifest['tools'])!={'python','git','node','openspec','databricks'}: raise ValueError()
        approved=json.loads(files('harness_local').joinpath('distribution_kit/official-tools.json').read_bytes())
        if manifest['tools']!=approved: raise ValueError()
        for tool in manifest['tools'].values():
            if not tool['license'] or manifest['files'].get(tool['artifact'])!=tool['sha256']: raise ValueError()
            if 'latest' in tool['url'] or not tool['url'].startswith('https://'): raise ValueError()
        if manifest['wheel'] not in manifest['files'] or manifest['skill'] not in manifest['files']: raise ValueError()
        return manifest
    except (OSError,ValueError,TypeError,KeyError,StopIteration,zipfile.BadZipFile):
        raise ConfigError('download_integrity_failed') from None
