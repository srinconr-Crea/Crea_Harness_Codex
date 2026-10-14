"""Run the standalone PowerShell entry point against controlled local kits."""
import json
from pathlib import Path
import subprocess

import pytest

SCRIPT=Path('src/harness_local/distribution_kit/install-harness.ps1').resolve()


def invoke(*args):
    assert SCRIPT.exists(), 'standalone installer missing'
    return subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','RemoteSigned','-File',str(SCRIPT),*map(str,args)],capture_output=True,text=True,timeout=60)


def test_preview_without_python_has_no_effects(scratch):
    root=scratch/'space runtime'; skill=scratch/'skills'
    result=invoke('-Kit',scratch/'missing-kit','-InstallRoot',root,'-SkillRoot',skill,'-Preview')
    assert result.returncode==0,result.stderr
    value=json.loads(result.stdout)
    assert value['command']=='install' and value['reason']=='tool_unavailable'
    assert value['certified'] is False and value['release_allowed'] is False
    assert not root.exists() and not skill.exists()


def test_manifest_rejects_unsupported_platform_and_missing_closure(scratch):
    import importlib
    assert importlib.util.find_spec('harness_local.installation') is not None, 'manifest validator missing'
    from harness_local.installation import validate_kit
    from harness_core.configuration import ConfigError
    kit=scratch/'kit'; kit.mkdir()
    (kit/'install-manifest.json').write_text(json.dumps(dict(schema_version=1,platform='linux',files={})))
    with pytest.raises(ConfigError): validate_kit(kit)


def test_invalid_kit_fails_before_install(scratch):
    root=scratch/'runtime'; skill=scratch/'skills'; kit=scratch/'kit'; kit.mkdir()
    (kit/'install-manifest.json').write_text('{}')
    result=invoke('-Kit',kit,'-InstallRoot',root,'-SkillRoot',skill,'-Apply')
    assert result.returncode!=0
    assert not root.exists() and not skill.exists()


def test_online_preview_is_a_plan_without_download_or_write(scratch):
    root=scratch/'runtime'; skill=scratch/'skills'
    value=invoke('-KitUrl','https://example.invalid/fixed-kit.zip','-KitSha256','a'*64,
        '-InstallRoot',root,'-SkillRoot',skill,'-Preview')
    assert value.returncode==0
    assert 'example.invalid' in value.stdout and 'a'*64 in value.stdout
    assert not root.exists() and not skill.exists()


@pytest.mark.parametrize('mutation',['version','missing_dependency','checksum'])
def test_fixed_kit_rejects_version_closure_and_checksum(scratch,mutation):
    import os
    from harness_core.configuration import ConfigError
    from harness_local.installation import validate_kit
    source=Path('dist/install-kit').resolve()
    if not (source/'install-manifest.json').exists(): pytest.skip('requires fixed kit protocol')
    kit=scratch/'kit'; kit.mkdir()
    manifest=json.loads((source/'install-manifest.json').read_bytes())
    # Read-only hard links avoid copying large official archives; no artifact
    # bytes are changed by these malformed-manifest cases.
    for name in manifest['files']:
        selected=kit/name; selected.parent.mkdir(parents=True,exist_ok=True)
        os.link(source/name,selected)
    if mutation=='version': manifest['version']='unexpected'
    elif mutation=='missing_dependency': manifest['runtime_dependencies'].pop()
    else: manifest['files'][manifest['wheel']]='0'*64
    (kit/'install-manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
    with pytest.raises(ConfigError,match='download_integrity_failed'): validate_kit(kit)


def test_offline_databricks_tool_preparation_is_absolute_and_repeatable(scratch,monkeypatch):
    import hashlib,socket
    from harness_core.onboarding_plan import canonical
    from harness_core.setup import InstallationRecord
    from harness_local.installation import validate_kit
    from harness_local.setup_tools import prepare
    source=Path('dist/install-kit').resolve()
    if not (source/'install-manifest.json').exists(): pytest.skip('requires fixed kit protocol')
    manifest=validate_kit(source); tool=manifest['tools']['databricks']
    root=scratch/'product'; root.mkdir(); journal=scratch/'journal'; journal.mkdir()
    marker=root/'customer-state.txt'; marker.write_bytes(b'preserve')
    record=InstallationRecord(schema_version=1,version='0.1.0',product_sha256='1'*64,
        installation_root=str(root),runtime_path=str(root/'runtime/python.exe'),skill_path=str(scratch/'SKILL.md'),
        tools=[],owned_files={},resource_installed=False,skill_discovered=False)
    entry=root/'installation.json'; entry.write_bytes(canonical(record.model_dump()))
    operation=dict(name='databricks',version=tool['version'],license=tool['license'],artifact=str(source/tool['artifact']),
        sha256=tool['sha256'],destination=str(root/('tools-databricks-'+tool['version'])),binary=tool['binary'],kind='zip')
    recipe=dict(existing=[],operations=[operation],blocked=False,installation_record=str(entry),kit_path=str(source),
        kit_sha256=hashlib.sha256((source/'install-manifest.json').read_bytes()).hexdigest())
    import zipfile
    actual_zip=zipfile.ZipFile; observed=[]
    def lease_checked_zip(path,*args,**kwargs):
        if str(path)==operation['artifact']:
            with pytest.raises(OSError):
                with open(path,'r+b'): pass
            observed.append(True)
        return actual_zip(path,*args,**kwargs)
    monkeypatch.setattr(zipfile,'ZipFile',lease_checked_zip)
    monkeypatch.setattr(socket,'create_connection',lambda *a,**k: (_ for _ in ()).throw(AssertionError('network forbidden')))
    tools,updated=prepare(recipe,journal)
    assert updated and Path(tools[0].path).is_absolute()
    checked=subprocess.run([tools[0].path,'--version'],capture_output=True,text=True,check=True)
    assert tool['version'] in checked.stdout
    repeated,digest=prepare(recipe,journal)
    assert repeated==tools and digest==updated and marker.read_bytes()==b'preserve'
    assert observed


def test_skill_rejects_modified_installed_code_before_python():
    root=Path('.test-data/i9').resolve(); skill=Path('.test-data/s9/harness-setup').resolve()
    if not (root/'installation.json').exists(): pytest.skip('requires isolated installed-wheel protocol')
    entry=skill/'invoke-setup.ps1'; code=root/'runtime/Lib/site-packages/harness_local/cli.py'
    old_entry=entry.read_bytes(); old_code=code.read_bytes(); old_record=(root/'installation.json').read_bytes()
    try:
        # Use the entry point under test with its expected ownership refreshed.
        entry.write_bytes(Path('src/harness_local/distribution_kit/invoke-setup.ps1').read_bytes())
        record=json.loads(old_record); import hashlib
        guard=skill/'fs-guard.dll'; guard.write_bytes(Path('src/harness_local/distribution_kit/fs-guard.dll').read_bytes())
        record['skill_files']['fs-guard.dll']=hashlib.sha256(guard.read_bytes()).hexdigest()
        record['skill_files']['invoke-setup.ps1']=hashlib.sha256(entry.read_bytes()).hexdigest()
        (root/'installation.json').write_text(json.dumps(record),encoding='utf-8')
        args=['powershell','-NoProfile','-ExecutionPolicy','RemoteSigned','-File',str(entry),'--help']
        control=subprocess.run(args,capture_output=True,text=True,timeout=60)
        if control.returncode:
            debug=skill/'invoke-debug.ps1'
            debug.write_bytes(entry.read_bytes().replace(b'} catch { Write-Output',b'} catch { Write-Output $_.Exception.Message; Write-Output'))
            diagnostic=subprocess.run([*args[:5],str(debug),'--help'],capture_output=True,text=True,timeout=60)
            assert control.returncode==0,control.stdout+diagnostic.stdout+diagnostic.stderr
        assert control.returncode==0,control.stderr
        code.write_bytes(b"raise RuntimeError('unexpected modified code')\n"+old_code)
        rejected=subprocess.run(args,capture_output=True,text=True,timeout=60)
        assert rejected.returncode==4 and 'owned_resource_conflict' in rejected.stdout
        assert 'unexpected modified code' not in rejected.stderr
    finally:
        (skill/'fs-guard.dll').unlink(missing_ok=True)
        (skill/'invoke-debug.ps1').unlink(missing_ok=True)
        code.write_bytes(old_code); entry.write_bytes(old_entry); (root/'installation.json').write_bytes(old_record)
