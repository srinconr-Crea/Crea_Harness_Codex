import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from harness_local.diagnostics import Check, aggregate, probe, inspect_target, doctor
from harness_local.onboarding import preview as actual_preview
from harness_local.cli import main


def preview(*args,**kwargs):
    return actual_preview(*args,**kwargs,probe_fn=lambda n:Check(n,'ready','compatible','local'))


def prepared(client):
    from harness_local.diagnostics import SKILLS
    p = client['target']
    (p/'openspec').mkdir()
    (p/'openspec/config.yaml').write_text('schema: spec-driven\n')
    for name in SKILLS:
        d=p/'.agents/skills'/name
        d.mkdir(parents=True)
        (d/'SKILL.md').write_text(f'---\nname: {name}\ndescription: workflow\nmetadata:\n  generatedBy: "1.13.2"\n---\nInstructions\n')


def snapshot(p):
    return {str(x.relative_to(p)):hashlib.sha256(x.read_bytes()).hexdigest()
            for x in p.rglob('*') if x.is_file()}


def test_probe_errors_and_limits(scratch):
    assert probe('git', executable=None).status == 'missing'
    for body, code in [('import time;time.sleep(2)','probe_timeout'),
                        ('print("x"*70000)','output_limit'), ('print("no version")','version_unrecognized')]:
        script=scratch/'probe.py'
        script.write_text(body)
        result=probe('git', executable=sys.executable, args=[str(script)], timeout=.15 if 'sleep' in body else 3)
        assert result.status=='error'
        assert result.code==code


def test_compatibility_and_aggregate(scratch):
    script=scratch/'version.py'
    script.write_text('print("openspec 1.13.1")')
    assert probe('openspec',executable=sys.executable,args=[str(script)]).status=='unsupported'
    assert aggregate([Check('a','ready','ok','ok')])==('ready',0)
    assert aggregate([Check('a','not_checked','pending','pending')])==('partial',0)
    assert aggregate([Check('a','missing','missing','missing'), Check('b','ready','ok','ok')])==('blocked',1)


def test_inspection_and_workflow_conflicts(client):
    prepared(client)
    assert all(c.status=='ready' for c in inspect_target(client['target']) if c.id.startswith('openspec'))
    p=client['target']/'.agents/skills/openspec-verify-change/SKILL.md'
    p.unlink()
    assert next(c for c in inspect_target(client['target']) if c.id.endswith('verify-change')).status=='missing'
    p.write_text('---\nname: openspec-verify-change\nmetadata:\n  generatedBy: "9.0"\n---\n')
    assert next(c for c in inspect_target(client['target']) if c.id.endswith('verify-change')).status=='unsupported'


def test_cli_json_and_invalid_flags(client,capsys):
    assert main(['init','--json'])==2
    assert json.loads(capsys.readouterr().out)['checks'][0]['code']=='apply_not_supported'
    assert main(['doctor','--json','--policy',str(client['policy'])])==2
    assert json.loads(capsys.readouterr().out)['status']=='invalid'
    assert main(['init','--dry-run','--json','--path',str(client['target'].parent/'absent'),
                 '--policy',str(client['policy']),'--binding',str(client['binding'])])==2
    assert json.loads(capsys.readouterr().out)['checks'][0]['code']=='target_not_found'


def test_prepared_preview_deterministic_and_read_only(client):
    prepared(client)
    root=client['target'].parent
    before=snapshot(root)
    a, code=preview(client['target'],client['policy'],client['binding'])
    b, again=preview(client['target'],client['policy'],client['binding'])
    assert a==b and code==again==0
    assert snapshot(root)==before
    assert any(x['path']=='AGENTS.md' and x['status']=='proposed' for x in a['actions'])
    assert all(x['status']=='existing' for x in a['actions'] if x['kind']=='openspec')
    (client['target']/'AGENTS.md').write_text('Custom instructions')
    report,code=preview(client['target'],client['policy'],client['binding'])
    assert code==1 and any(x['status']=='conflict' for x in report['actions'])


def test_unprepared_second_client(client):
    from harness_core.configuration import ConfigError
    target=client['target']
    subprocess.run(['git','-C',str(target),'remote','set-url','origin','https://github.com/demo/beta.git'],check=True)
    (target/'.harness/client.yaml').unlink()
    data=json.loads(client['policy'].read_text())
    data.update(client_id='beta',repository='demo/beta')
    client['policy'].write_text(json.dumps(data))
    data=json.loads(client['binding'].read_text())
    data.update(client_id='beta',state_dir=str(target.parent/'state/beta/checkout'),
                policy_sha256=hashlib.sha256(client['policy'].read_bytes()).hexdigest())
    client['binding'].write_text(json.dumps(data))
    with pytest.raises(ConfigError,match='descriptor_input_required'):
        preview(target,client['policy'],client['binding'])
    # If imported or executed this client file fails the test and changes the snapshot.
    (target/'sitecustomize.py').write_text('raise RuntimeError("CLIENT_EXECUTED")')
    before=snapshot(target.parent)
    result,code=preview(target,client['policy'],client['binding'],repo='demo/beta',base_branch='develop')
    assert code==1 and snapshot(target.parent)==before
    proposal=next(x for x in result['actions'] if x['path']=='.harness/client.yaml')
    assert json.loads(proposal['content'])['client_id']=='beta'
    assert 'alpha' not in proposal['content']


def test_doctor_injected_no_effects(client):
    prepared(client)
    before=snapshot(client['target'].parent)
    calls=[]
    def fake(name):
        calls.append(name)
        return Check(name,'ready','compatible','local')
    report,code=doctor(client['target'],client['policy'],client['binding'],probe_fn=fake)
    assert code==0 and report['status']=='partial'
    assert set(calls)=={'python','git','node','openspec','databricks'}
    assert any(c['id']=='databricks_auth' and c['status']=='not_checked' for c in report['checks'])
    assert snapshot(client['target'].parent)==before


def test_worktree_checkout(client):
    p=client['target']
    subprocess.run(['git','-C',str(p),'add','.harness/client.yaml'],check=True)
    subprocess.run(['git','-C',str(p),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                    'commit','-m','fixture'],check=True,capture_output=True)
    w=p.parent/'worktree'
    subprocess.run(['git','-C',str(p),'worktree','add','-b','feature/test',str(w)],check=True,capture_output=True)
    assert (w/'.git').is_file()
    checks=inspect_target(w)
    assert next(c for c in checks if c.id=='git_checkout').status=='ready'
    subprocess.run(['git','-C',str(w),'checkout','--detach'],check=True,capture_output=True)
    assert next(c for c in inspect_target(w) if c.id=='git_branch').code=='detached'


def test_preview_tool_failure_preserves_other_checks(client):
    prepared(client)
    report,code=actual_preview(client['target'],client['policy'],client['binding'],
        probe_fn=lambda n:Check(n,'missing' if n=='node' else 'ready','fake','fake'))
    assert code==1 and report['status']=='blocked'
    assert any(c['id']=='git' and c['status']=='ready' for c in report['checks'])


def test_schema_files_match():
    from harness_core.contracts import Descriptor,Policy,Binding
    for model in (Descriptor,Policy,Binding):
        assert json.loads((Path('schemas')/(model.__name__.lower()+'.schema.json')).read_text())==model.model_json_schema()


def test_git_status_never_executes_client_filter(client,monkeypatch):
    p=client['target']
    marker=p.parent/'filter-executed'
    script=p/'filter.py'
    script.write_text('from pathlib import Path\nPath('+repr(str(marker))+').touch()\nimport sys\nsys.stdout.write(sys.stdin.read())\n')
    (p/'.gitattributes').write_text('tracked.txt filter=evil\n')
    (p/'tracked.txt').write_text('before\n')
    # Stage before registering the malicious driver.
    subprocess.run(['git','-C',str(p),'add','.'],check=True,capture_output=True)
    subprocess.run(['git','-C',str(p),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                    'commit','-m','fixture'],check=True,capture_output=True)
    command='"'+sys.executable+'" "'+str(script)+'"'
    subprocess.run(['git','-C',str(p),'config','filter.evil.clean',command],check=True)
    (p/'tracked.txt').write_text('after!\n')
    import os,time
    stamp=time.time()+5
    os.utime(p/'tracked.txt',(stamp,stamp))
    subprocess.run(['git','-C',str(p),'hash-object','--path=tracked.txt','tracked.txt'],check=True,capture_output=True)
    assert marker.exists(), 'Control positivo: Git debe ejecutar el filtro de la fixture'
    marker.unlink()
    import harness_local.diagnostics as diagnostics
    original=diagnostics.run_bounded
    def checked(argv,*args,**kwargs):
        if 'status' in argv:
            assert 'filter.evil.clean=' in argv
            assert 'filter.evil.process=' in argv
            assert 'filter.evil.required=false' in argv
        return original(argv,*args,**kwargs)
    monkeypatch.setattr(diagnostics,'run_bounded',checked)
    inspect_target(p)
    assert not marker.exists()


@pytest.mark.parametrize('body',[
    b'---\nname: openspec-verify-change\nmetadata: '+b'['*600+b'x'+b']'*600+b'\n---\n',
    b'---\nname: \xff\n---\n'],ids=['deeply-nested','invalid-utf8'])
def test_invalid_skill_frontmatter_is_incompatible(client,body):
    prepared(client)
    (client['target']/'.agents/skills/openspec-verify-change/SKILL.md').write_bytes(body)
    checks=inspect_target(client['target'])
    assert next(c for c in checks if c.id=='openspec-verify-change').status=='unsupported'


def test_human_preview_represents_json(client,capsys,monkeypatch):
    prepared(client)
    import harness_local.cli as cli
    monkeypatch.setattr(cli,'preview',preview)
    args=['init','--dry-run','--path',str(client['target']),'--policy',str(client['policy']),'--binding',str(client['binding'])]
    assert main(args+['--json'])==0
    report=json.loads(capsys.readouterr().out)
    assert main(args)==0
    text=capsys.readouterr().out
    assert report['identities']['client_id'] in text
    for value in report['input_hashes'].values():
        assert value in text
    for action in report['actions']:
        if 'sha256' in action:
            assert action['sha256'] in text and action['content'] in text


def test_native_diagnostic_and_preview_no_global_effects(client,monkeypatch):
    prepared(client)
    import harness_local.diagnostics as diagnostics
    root=client['target'].parent
    global_dir=root/'global'
    global_dir.mkdir()
    (global_dir/'existing-config').write_text('UNCHANGED')
    for name in ('HOME','USERPROFILE','APPDATA','LOCALAPPDATA','XDG_CONFIG_HOME','XDG_CACHE_HOME','CODEX_HOME'):
        monkeypatch.setenv(name,str(global_dir))
    calls=[]
    original=diagnostics.run_bounded
    def checked(argv,*args,**kwargs):
        assert not kwargs.get('shell',False)
        if Path(argv[0]).stem.lower()=='git' and argv[-1]!='--version':
            assert '-C' in argv
            operation=argv[argv.index('-C')+2]
            assert operation in ('rev-parse','symbolic-ref','remote','status','config')
            if operation=='remote':
                assert argv[-2:]==['get-url','origin']
            if operation=='config':
                assert '--get-regexp' in argv
        else:
            assert argv[-1]=='--version'
        calls.append(argv)
        return original(argv,*args,**kwargs)
    monkeypatch.setattr(diagnostics,'run_bounded',checked)
    before=snapshot(root)
    doctor(client['target'],client['policy'],client['binding'])
    actual_preview(client['target'],client['policy'],client['binding'])
    assert snapshot(root)==before and calls


def test_cli_doctor_exit_codes_and_sanitization(client,monkeypatch,capsys):
    import harness_local.cli as cli
    from harness_local.diagnostics import report
    for expected,status in ((0,'ready'),(1,'missing')):
        monkeypatch.setattr(cli,'doctor',lambda *args:report('doctor',[Check('node',status,'fixture','fixture')]))
        assert main(['doctor','--json'])==expected
        assert json.loads(capsys.readouterr().out)['checks'][0]['status']==status
    client['policy'].write_text('password: SUPER_SECRET')
    assert main(['init','--dry-run','--json','--path',str(client['target']),
        '--policy',str(client['policy']),'--binding',str(client['binding'])])==2
    output=capsys.readouterr().out
    assert 'SUPER_SECRET' not in output
    assert json.loads(output)['status']=='invalid'


def test_non_git_target_and_redundant_identity_flags(client,scratch):
    from harness_core.configuration import ConfigError
    directory=scratch/'ordinary-directory'
    directory.mkdir()
    with pytest.raises(ConfigError,match='not_git_checkout'):
        preview(directory,client['policy'],client['binding'])
    with pytest.raises(ConfigError,match='descriptor_input_conflict'):
        preview(client['target'],client['policy'],client['binding'],repo='demo/other')


def test_codex_presence_and_divergent_workflow_preview(client):
    prepared(client)
    p=client['target']
    (p/'.codex').mkdir()
    (p/'.codex/config.toml').write_text('[agents]\n')
    (p/'.agents/skills/openspec-verify-change/SKILL.md').write_text('---\nname: openspec-verify-change\nmetadata:\n  generatedBy: "9.0"\n---\n')
    before=snapshot(p.parent)
    result,code=preview(p,client['policy'],client['binding'])
    assert code==1
    assert any(c['id']=='codex_files' and c['code']=='present' and c['status']=='not_checked' for c in result['checks'])
    assert any(a['path']=='.agents/skills/openspec-verify-change/SKILL.md' and a['status']=='conflict' for a in result['actions'])
    assert '.codex/config.toml' in result['input_hashes'] and snapshot(p.parent)==before
