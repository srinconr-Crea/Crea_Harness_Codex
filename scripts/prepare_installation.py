"""Build a pinned, offline Windows installation kit from official artifacts.

Requires the reviewed local Node/npm only when creating the npm closure first.
Subsequent builds consume the checked-in lock with npm ci and fixed versions.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]
KIT=ROOT/'dist/install-kit'
DATA=ROOT/'src/harness_local/distribution_kit'
TOOLS={
 'python':dict(version='3.13.7',artifact='tools/python-3.13.7-amd64.exe',
    url='https://www.python.org/ftp/python/3.13.7/python-3.13.7-amd64.exe',
    sha256='b12e2e82461ac8e51fc43289050bc8eb937a32d84ce4d242e2c88258c37cf2bb',license='PSF',binary='python.exe'),
 'git':dict(version='2.51.0',artifact='tools/PortableGit-2.51.0-64-bit.7z.exe',
    url='https://github.com/git-for-windows/git/releases/download/v2.51.0.windows.1/PortableGit-2.51.0-64-bit.7z.exe',
    sha256='a09b275d51ed3e829128e04cf4168fb54896cf6234bb30fecb8dc96a2bd321fa',license='GPL-2.0',binary='cmd/git.exe'),
 'node':dict(version='22.20.0',artifact='tools/node-v22.20.0-win-x64.zip',
    url='https://nodejs.org/dist/v22.20.0/node-v22.20.0-win-x64.zip',
    sha256='bb819d6eb8f5bfda294bbc83a7e4ec6539da67c4233d54b0d655b9248b15e29d',license='MIT + bundled licenses',binary='node-v22.20.0-win-x64/node.exe'),
 'databricks':dict(version='0.292.0',artifact='tools/databricks_cli_0.292.0_windows_amd64.zip',
    url='https://github.com/databricks/cli/releases/download/v0.292.0/databricks_cli_0.292.0_windows_amd64.zip',
    sha256='14de87368dad80892ec793494877a59317e7fb4522c87cd7cf4e093b09aa2fb2',license='Databricks License (LICENSE retained)',binary='databricks.exe')}


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def download(tool):
    out=KIT/tool['artifact']; out.parent.mkdir(parents=True,exist_ok=True)
    if not out.exists():
        with urllib.request.urlopen(tool['url'],timeout=60) as source, out.open('xb') as target:
            shutil.copyfileobj(source,target)
    if digest(out)!=tool['sha256']: raise ValueError('download_integrity_failed: '+out.name)


def main():
    KIT.mkdir(parents=True,exist_ok=True)
    for tool in TOOLS.values(): download(tool)
    stage=ROOT/'dist/npmstage'; stage.mkdir(exist_ok=True)
    (stage/'package.json').write_text(json.dumps({'name':'harness-openspec-runtime','version':'1.0.0','private':True,
        'dependencies':{'@fission-ai/openspec':'1.13.2'}}))
    lock=DATA/'openspec-package-lock.json'
    npm=shutil.which('npm.cmd')
    if not npm: raise ValueError('Node/npm needed to build the kit, not to install it')
    args=[npm,'--cache',str(ROOT/'dist/npmcache'),'--userconfig',str(ROOT/'dist/empty.npmrc'),
          '--globalconfig',str(ROOT/'dist/empty-global.npmrc'),'--prefix',str(stage)]
    for name in ('empty.npmrc','empty-global.npmrc'): (ROOT/'dist'/name).touch()
    if lock.exists(): shutil.copyfile(lock,stage/'package-lock.json')
    else:
        subprocess.run([*args,'install','--package-lock-only','--ignore-scripts','--no-audit','--no-fund'],check=True)
        shutil.copyfile(stage/'package-lock.json',lock)
    closure=json.loads(lock.read_bytes())
    for name,package in closure['packages'].items():
        if not name: continue
        if not package.get('resolved','').startswith('https://registry.npmjs.org/') or not package.get('integrity','').startswith('sha512-'):
            raise ValueError('unverified npm artifact')
    subprocess.run([*args,'ci','--ignore-scripts','--no-audit','--no-fund','--omit=dev'],check=True)
    # A reproducible archive of the exact npm closure. All LICENSE/NOTICE files
    # remain in the package tree; npm verifies each official tarball integrity.
    archive=KIT/'tools/openspec-1.13.2.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as out:
        for path in sorted(stage.rglob('*')):
            if not path.is_file(): continue
            name=path.relative_to(stage).as_posix()
            info=zipfile.ZipInfo(name,date_time=(2026,10,14,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED
            out.writestr(info,path.read_bytes())
    TOOLS['openspec']=dict(version='1.13.2',artifact='tools/openspec-1.13.2.zip',
        url='https://registry.npmjs.org/@fission-ai/openspec/-/openspec-1.13.2.tgz',
        sha256=digest(archive),license='MIT + per-package licenses retained; closure: openspec-package-lock.json',
        binary='node_modules/@fission-ai/openspec/bin/openspec.js')
    (DATA/'official-tools.json').write_text(json.dumps(TOOLS,indent=2)+'\n',encoding='utf-8')
    manifest=json.loads((DATA/'candidate.json').read_bytes())
    dependencies=[{k:v for k,v in d.items() if k!='schema_version'} for d in manifest['dependencies']]
    for dep in dependencies:
        dest=KIT/'wheelhouse'/dep['artifact']; dest.parent.mkdir(exist_ok=True)
        shutil.copyfile(ROOT/'dist/wheelhouse'/dep['artifact'],dest)
    subprocess.run([sys.executable,'-m','build','--wheel','--no-isolation'],cwd=ROOT,check=True,
        env=dict(os.environ,SOURCE_DATE_EPOCH='1791936000'))
    wheels=list((ROOT/'dist').glob('crea_local_harness-*.whl'))
    if len(wheels)!=1: raise ValueError('ambiguous wheel')
    shutil.copyfile(wheels[0],KIT/wheels[0].name)
    for name in ('install-harness.ps1','runtime-lock.txt','harness-setup.md','invoke-setup.ps1','openspec-package-lock.json','fs-guard.dll'):
        shutil.copyfile(DATA/name,KIT/name)
    script=(KIT/'install-harness.ps1').read_text(encoding='utf-8')
    (KIT/'install-harness.ps1').write_text(script.replace('__OPENSPEC_ZIP_SHA256__',TOOLS['openspec']['sha256']).replace('__FS_GUARD_SHA256__',digest(DATA/'fs-guard.dll')),encoding='utf-8')
    expected={'install-harness.ps1','runtime-lock.txt','harness-setup.md','invoke-setup.ps1','openspec-package-lock.json','fs-guard.dll',wheels[0].name}
    expected.update('wheelhouse/'+d['artifact'] for d in dependencies)
    expected.update(t['artifact'] for t in TOOLS.values())
    files={name:digest(KIT/name) for name in sorted(expected)}
    result=dict(schema_version=1,version='0.1.0',platform='windows-amd64',files=files,tools=TOOLS,
        runtime_dependencies=dependencies,wheel=wheels[0].name,skill='harness-setup.md')
    (KIT/'install-manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    (DATA/'official-tools.json').write_text(json.dumps(TOOLS,indent=2)+'\n',encoding='utf-8')
    bundle=ROOT/'dist/install-kit-0.1.0-windows-amd64.zip'
    with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED) as out:
        for name in sorted(expected|{'install-manifest.json'}):
            info=zipfile.ZipInfo(name,date_time=(2026,10,14,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED
            out.writestr(info,(KIT/name).read_bytes())
    print(json.dumps({'files':len(files),'npm_packages':len(closure['packages'])-1,'kit':str(KIT),
        'manifest_sha256':digest(KIT/'install-manifest.json'),'bundle_sha256':digest(bundle)}))


if __name__=='__main__': main()
