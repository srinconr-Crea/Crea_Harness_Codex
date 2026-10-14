"""Prepare a Windows cp313 candidate and a reviewed offline runtime lock."""
import importlib.metadata as metadata
import json
from pathlib import Path
import subprocess
import sys
import zipfile

from harness_core.distribution import ReleaseManifest, PROTOCOLS
from harness_core.onboarding_plan import canonical, sha

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT/'src/harness_local/distribution_kit'
WHEELS = ROOT/'dist/wheelhouse'
NAMES = ('pydantic', 'pydantic_core', 'PyYAML', 'annotated-types', 'typing_extensions', 'typing-inspection')


def main():
    KIT.mkdir(exist_ok=True)
    WHEELS.mkdir(parents=True, exist_ok=True)
    versions = {name:metadata.version(name) for name in NAMES}
    subprocess.run([sys.executable, '-m', 'pip', 'download', '--only-binary=:all:', '--no-deps',
        '--dest', str(WHEELS), *[f'{n}=={v}' for n,v in versions.items()]], check=True)
    dependencies=[]
    lock=[]
    for name, version in versions.items():
        prefix=name.lower().replace('-', '_')+'-'+version+'-'
        matches=[p for p in WHEELS.glob('*.whl') if p.name.lower().startswith(prefix)]
        if len(matches) != 1: raise ValueError('ambiguous_wheel: '+name)
        wheel=matches[0]
        with zipfile.ZipFile(wheel) as archive:
            meta=archive.read(next(p for p in archive.namelist() if p.endswith('.dist-info/METADATA'))).decode()
        license=next((line.split(': ',1)[1] for line in meta.splitlines() if line.startswith(('License-Expression: ', 'License: '))), 'license_in_wheel')
        digest=sha(wheel.read_bytes())
        dependencies.append(dict(schema_version=1,name=name,version=version,sha256=digest,license=license,artifact=wheel.name))
        lock.append(f'{name}=={version} --hash=sha256:{digest}')
    (KIT/'runtime-lock.txt').write_text('\n'.join(lock)+'\n',encoding='utf-8')
    root=KIT.parent
    resources={p.relative_to(root).as_posix():sha(p.read_bytes()) for folder in
        ('quality_kit','desktop_kit','guided_kit','validation_kit','story_kit','openspec_kit','templates','distribution_kit')
        for p in sorted((root/folder).rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='candidate.json'}
    resources.update({p.name:sha(p.read_bytes()) for p in sorted(root.glob('*.py'))})
    core=ROOT/'src/harness_core'
    resources.update({'harness_core/'+p.relative_to(core).as_posix():sha(p.read_bytes())
        for p in sorted(core.rglob('*')) if p.is_file() and p.suffix in ('.py','.json') and '__pycache__' not in p.parts})
    source_path=root/'quality_kit/vendor/databricks-agent-skills/SOURCE.json'
    provenance=json.loads(source_path.read_bytes())
    sources=[dict(schema_version=1,name='databricks-agent-skills',commit=provenance['commit'],
        sha256=sha(source_path.read_bytes()),license='Databricks License (LICENSE/NOTICE conservados)')]
    value=dict(schema_version=1,kind='release_candidate',version=metadata.version('crea-local-harness'),
        base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        resources=resources,dependencies=dependencies,sources=sources,certified=False,release_allowed=False,
        pending_acceptance=list(PROTOCOLS))
    manifest=ReleaseManifest.model_validate({**value,'manifest_sha256':sha(canonical(value))})
    (KIT/'candidate.json').write_bytes(json.dumps(manifest.model_dump(),indent=2,ensure_ascii=False).encode()+b'\n')
    print(json.dumps(dict(resources=len(resources),dependencies=len(dependencies),manifest_sha256=manifest.manifest_sha256)))


if __name__ == '__main__': main()
