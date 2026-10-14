import importlib
import json
from pathlib import Path

import pytest

from harness_core.configuration import ConfigError
from harness_core.onboarding_plan import canonical
from test_setup_contracts import inputs
from test_guided_onboarding import setup,ready


def api():
    assert importlib.util.find_spec('harness_local.environment_setup') is not None, 'setup facade missing'
    return importlib.import_module('harness_local.environment_setup')


def supplied(client, **updates):
    from harness_core.guided import collect,GuidedRequest
    draft,_,_=setup(client)
    data=inputs(client)
    data['guided_request']=GuidedRequest.model_validate(dict(schema_version=1,**collect(draft)['values'])).model_dump()
    data['access_scope'].update(read_allow=['src/','tests/'],write_allow=['src/','tests/'],deny=[])
    return {**data,**updates}


def snapshot(path):
    return {p.relative_to(path).as_posix():p.read_bytes() for p in path.rglob('*') if p.is_file()}


def test_import_complete_and_missing_decisions(client):
    result=api().interview(supplied(client))
    assert result['questions']==[] and result['status']=='ready'
    result=api().interview({'schema_version':1,'descriptor':str(client['target']/'.harness/client.yaml')})
    assert result['values']['descriptor']['repository']=='demo/alpha'
    assert 'descriptor' not in {q['field'] for q in result['questions']}
    assert {'policy','binding','access_scope','guided_request'}<={q['field'] for q in result['questions']}


def test_preview_and_parent_export_only(client,scratch):
    m=api(); data=supplied(client); before=snapshot(scratch)
    result,code=m.preview(data,probe_fn=ready)
    assert code==0 and result['plan']['applicable']
    assert result['plan']['child_plans']
    assert '.harness/client.yaml' in result['plan']['technical_reads']
    assert snapshot(scratch)==before
    exported=scratch/'setup-parent.json'
    m.preview(data,probe_fn=ready,plan_out=exported)
    assert set(snapshot(scratch))-set(before)=={'setup-parent.json'}
    assert not Path(json.loads(client['binding'].read_text())['state_dir']).exists()


def test_reviewed_apply_and_status(client,scratch):
    m=api(); parent=scratch/'parent.json'
    result,_=m.preview(supplied(client),probe_fn=ready,plan_out=parent)
    with pytest.raises(ConfigError,match='plan_stale'): m.apply(parent,'0'*64,probe_fn=ready)
    assert not (client['target']/'AGENTS.md').exists()
    applied,code=m.apply(parent,result['plan']['plan_sha256'],probe_fn=ready)
    assert applied['report']['prepared'] and code==0
    assert not applied['report']['certified'] and not applied['report']['publication_allowed']
    assert m.status(parent)[0]['report']['prepared']
    assert m.apply(parent,result['plan']['plan_sha256'],probe_fn=ready)[0]['idempotent']
    assert client['binding'].with_name(client['binding'].name+'.setup.json').exists()
    assert any(c['reason']=='remote_not_checked' for c in applied['report']['capabilities'])


def test_drift_and_preserved_personal_agents(client,scratch):
    m=api(); (client['target']/'AGENTS.md').write_text('Reglas propias\n',encoding='utf-8')
    parent=scratch/'parent.json'
    result,_=m.preview(supplied(client),probe_fn=ready,plan_out=parent)
    (client['target']/'AGENTS.md').write_text('Nueva personalización\n',encoding='utf-8')
    with pytest.raises(ConfigError): m.apply(parent,result['plan']['plan_sha256'],probe_fn=ready)
    assert (client['target']/'AGENTS.md').read_text(encoding='utf-8')=='Nueva personalización\n'


def test_existing_scope_drift_is_rejected_before_state_or_target_write(client,scratch):
    m=api(); data=supplied(client)
    scope=client['target']/'.harness/access-scope.json'
    from harness_core.setup import AccessScope
    scope.write_bytes(canonical(AccessScope.model_validate(data['access_scope']).model_dump())+b'\n')
    parent=scratch/'parent.json'
    value,code=m.preview(data,probe_fn=ready,plan_out=parent); assert code==0
    scope.write_bytes(b'changed after review')
    before=snapshot(scratch)
    with pytest.raises(ConfigError,match='plan_stale'): m.apply(parent,value['plan']['plan_sha256'],probe_fn=ready)
    assert snapshot(scratch)==before


def test_partial_auth_preserves_prepared(client,scratch):
    m=api(); parent=scratch/'parent.json'
    result,_=m.preview(supplied(client,capabilities=['local','databricks']),probe_fn=ready,plan_out=parent)
    applied,code=m.apply(parent,result['plan']['plan_sha256'],probe_fn=ready)
    assert applied['report']['prepared']
    remote=next(c for c in applied['report']['capabilities'] if c['id']=='databricks')
    assert remote['status']=='not_checked' and remote['reason']=='remote_not_checked'


def test_resume_after_stage_failure_preserves_customization(client,scratch,monkeypatch):
    m=api(); parent=scratch/'parent.json'
    result,_=m.preview(supplied(client),probe_fn=ready,plan_out=parent)
    def fail(stage):
        if stage=='before_integrate': raise ConfigError('tool_unavailable')
    monkeypatch.setattr(m,'checkpoint',fail)
    with pytest.raises(ConfigError): m.apply(parent,result['plan']['plan_sha256'],probe_fn=ready)
    assert m.status(parent)[0]['report']['prepared']
    monkeypatch.setattr(m,'checkpoint',lambda _:None)
    recovered,_=m.recover(parent,result['plan']['plan_sha256'],probe_fn=ready)
    assert recovered['report']['prepared']
    assert (client['target']/'AGENTS.md').exists()


@pytest.mark.parametrize('point',['after_prepare','after_integrate'])
def test_resume_after_completed_child_effect(client,scratch,monkeypatch,point):
    m=api(); parent=scratch/'parent.json'
    value,_=m.preview(supplied(client),probe_fn=ready,plan_out=parent)
    monkeypatch.setattr(m,'checkpoint',lambda stage: (_ for _ in ()).throw(ConfigError('recovery_required')) if stage==point else None)
    with pytest.raises(ConfigError): m.apply(parent,value['plan']['plan_sha256'],probe_fn=ready)
    monkeypatch.setattr(m,'checkpoint',lambda _:None)
    recovered,code=m.recover(parent,value['plan']['plan_sha256'],probe_fn=ready)
    assert code==0 and recovered['report']['prepared']
    assert m.apply(parent,value['plan']['plan_sha256'],probe_fn=ready)[0]['idempotent']


def test_expired_receipt_does_not_report_available(client,scratch):
    from datetime import datetime,timedelta,timezone
    from harness_local.execution_state import persist
    m=api(); parent=scratch/'parent.json'
    value,_=m.preview(supplied(client),probe_fn=ready,plan_out=parent)
    m.apply(parent,value['plan']['plan_sha256'],probe_fn=ready)
    plan=m.select(parent); run=m.journal(plan)
    evidence=run.observations['local']['evidence'][0]
    evidence['observed_at']=(datetime.now(timezone.utc)-timedelta(days=2)).isoformat()
    evidence['valid_until']=(datetime.now(timezone.utc)-timedelta(days=1)).isoformat()
    persist(m.folder(plan)/'journal.json',run)
    report=m.status(parent)[0]['report']
    assert next(c['status'] for c in report['capabilities'] if c['id']=='local')=='not_checked'
    assert 'local_clean' not in report['hu_admissible']


def test_private_git_used_when_path_has_no_git(client,scratch,monkeypatch):
    import hashlib,shutil,subprocess,sys
    from harness_core.setup import InstallationRecord
    m=api(); data=supplied(client)
    git=shutil.which('git'); version=subprocess.run([git,'--version'],capture_output=True,text=True,check=True).stdout.strip().split()[-1]
    skill=scratch/'SKILL.md'; skill.write_bytes(b'generic')
    record=InstallationRecord(schema_version=1,version='0.1.0',product_sha256='1'*64,
        installation_root=str(Path(sys.executable).parent.parent),runtime_path=sys.executable,skill_path=str(skill),
        skill_sha256=hashlib.sha256(b'generic').hexdigest(),resource_installed=True,skill_discovered=False,owned_files={},
        tools=[dict(schema_version=1,name='git',version=version,path=git,sha256=hashlib.sha256(Path(git).read_bytes()).hexdigest(),license='GPL-2.0')])
    entry=scratch/'installation.json'; entry.write_bytes(canonical(record.model_dump())); data['installation_record']=str(entry)
    monkeypatch.setattr(shutil,'which',lambda _:None)
    parent=scratch/'parent.json'
    result,code=m.preview(data,probe_fn=ready,plan_out=parent)
    assert code==0
    applied,code=m.apply(parent,result['plan']['plan_sha256'],probe_fn=ready)
    assert code==0 and applied['report']['prepared']


def test_unrelated_staged_change_blocks_before_setup_effect(client,scratch):
    import subprocess
    m=api(); data=supplied(client,commit_local=True)
    git=lambda *args:subprocess.run(['git','-C',str(client['target']),*args],capture_output=True,check=True)
    git('add','.harness/client.yaml'); git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','base')
    (client['target']/'business.py').write_bytes(b'user-change')
    git('add','business.py')
    before=snapshot(scratch)
    result,code=m.preview(data,probe_fn=ready)
    assert code==4 and result['plan']['applicable'] is False
    assert snapshot(scratch)==before


def test_unrelated_dirty_checkout_is_blocked_without_effects(client,scratch):
    m=api(); data=supplied(client)
    (client['target']/'unreviewed.py').write_text('customer work',encoding='utf-8')
    before=snapshot(scratch)
    value,code=m.preview(data,probe_fn=ready)
    assert code==4 and 'owned_resource_conflict' in value['plan']['blockers']
    assert snapshot(scratch)==before


def test_future_checkout_recipe_uses_known_repository_decisions(client,scratch):
    from harness_core.setup import SetupInput
    from harness_local.setup_recipe import recipe
    m=api(); data=supplied(client)
    future=scratch/'future'; data['clone']=True
    data['binding']['target_path']=str(future)
    data['guided_request']['target_path']=str(future)
    data['guided_request'].update(repository=data['descriptor']['repository'],base_branch=data['descriptor']['base_branch'])
    client['binding'].write_bytes(canonical(data['binding']))
    value,code=m.preview(data,probe_fn=ready)
    assert code==0
    frozen=json.loads(value['plan']['child_payloads']['managed_recipe'])
    assert frozen==recipe(SetupInput.model_validate(data))
    assert set(frozen['prepare'])|set(frozen['integrate'])<set(value['plan']['integration_writes'])
    assert not future.exists()


def test_clone_materializes_only_frozen_child_scope(client,scratch,monkeypatch):
    import subprocess
    m=api(); data=supplied(client); source=client['target']; future=scratch/'cloned'
    subprocess.run(['git','-C',str(source),'add','.harness/client.yaml'],check=True,capture_output=True)
    subprocess.run(['git','-C',str(source),'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','base'],check=True,capture_output=True)
    data.update(clone=True)
    data['binding']['target_path']=str(future); data['guided_request']['target_path']=str(future)
    client['binding'].write_bytes(canonical(data['binding']))
    actual=subprocess.run
    def local_remote(args,**kwargs):
        if 'clone' in args:
            selected=list(args); selected[-2]=str(source)
            output=actual(selected,**kwargs)
            assert output.returncode==0,output.stderr
            actual([args[0],'-C',str(future),'remote','set-url','origin',data['repository_url']],check=True,capture_output=True)
            return output
        return actual(args,**kwargs)
    monkeypatch.setattr(subprocess,'run',local_remote)
    parent=scratch/'parent-clone.json'
    value,code=m.preview(data,probe_fn=ready,plan_out=parent); assert code==0
    output,code=m.apply(parent,value['plan']['plan_sha256'],probe_fn=ready)
    assert code==0 and output['report']['prepared']
    child=json.loads(Path(m.journal(m.select(parent)).child_path).read_text())
    assert {o['path'] for o in child['preparation']['operations'] if o['scope']=='target'}<=set(value['plan']['integration_writes'])


@pytest.mark.parametrize('failure,reason',[('login','auth_pending'),('read','permission_conflict')])
def test_native_oauth_failure_keeps_local_preparation_and_redacts(client,scratch,monkeypatch,failure,reason):
    import hashlib,subprocess,sys
    from harness_core.setup import InstallationRecord
    m=api(); data=supplied(client,capabilities=['local','databricks'],remote_read=True,databricks_host='https://example.invalid')
    data['binding']['databricks_profile']='synthetic'; client['binding'].write_bytes(canonical(data['binding']))
    binary=Path(sys.executable); skill=scratch/'SKILL.md'; skill.write_bytes(b'generic')
    record=InstallationRecord(schema_version=1,version='0.1.0',product_sha256='1'*64,
        installation_root=str(binary.parent.parent),runtime_path=str(binary),skill_path=str(skill),
        skill_sha256=hashlib.sha256(b'generic').hexdigest(),resource_installed=True,skill_discovered=False,owned_files={},
        tools=[dict(schema_version=1,name='databricks',version='0.292.0',path=str(binary),sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),license='synthetic-double')])
    entry=scratch/'installation.json'; entry.write_bytes(canonical(record.model_dump())); data['installation_record']=str(entry)
    actual=subprocess.run; commands=[]
    def native(args,**kwargs):
        if args[0]==str(binary):
            commands.append(args[1:])
            bad=('auth' in args and failure=='login') or ('current-user' in args and failure=='read')
            return subprocess.CompletedProcess(args,1 if bad else 0,b'0.292.0',b'secret-output-that-must-not-be-retained')
        return actual(args,**kwargs)
    monkeypatch.setattr(subprocess,'run',native)
    parent=scratch/'oauth-parent.json'
    value,code=m.preview(data,probe_fn=ready,plan_out=parent); assert code==0
    output,code=m.apply(parent,value['plan']['plan_sha256'],probe_fn=ready)
    assert code==3 and output['report']['prepared'] and output['reason']==reason
    assert reason==next(c['reason'] for c in output['report']['capabilities'] if c['id']=='databricks')
    assert all(not ({'jobs','deploy','run'}&set(command)) for command in commands)
    assert b'secret-output-that-must-not-be-retained' not in b''.join(snapshot(scratch).values())


def test_missing_databricks_is_planned_from_pinned_offline_kit(client,scratch,monkeypatch):
    import shutil,hashlib,sys
    from harness_core.setup import InstallationRecord
    which=shutil.which
    monkeypatch.setattr(shutil,'which',lambda name:None if name=='databricks' else which(name))
    kit=Path('dist/install-kit').resolve()
    if not (kit/'install-manifest.json').exists(): pytest.skip('requires pinned kit protocol')
    skill=scratch/'SKILL.md'; skill.write_bytes(b'synthetic resource')
    record=InstallationRecord(schema_version=1,version='0.1.0',product_sha256='1'*64,
        installation_root=str(Path(sys.executable).parent.parent),runtime_path=sys.executable,skill_path=str(skill),
        skill_sha256=hashlib.sha256(skill.read_bytes()).hexdigest(),tools=[],owned_files={},resource_installed=True,skill_discovered=False)
    entry=scratch/'installation.json'; entry.write_bytes(canonical(record.model_dump()))
    data=supplied(client,capabilities=['local','databricks'],installation_kit=str(kit),installation_record=str(entry))
    before=snapshot(scratch)
    result,code=api().preview(data,probe_fn=ready)
    assert code==0
    effects=result['plan']['effects']
    assert any(e['kind']=='install' and 'databricks' in e['destination'] for e in effects)
    assert result['plan']['child_payloads']['tools']
    assert snapshot(scratch)==before


def test_two_clients_and_supported_custom_instructions_are_preserved(client,scratch):
    import subprocess
    from conftest import client as factory
    from harness_core.desktop import activate_profiles
    from harness_local.desktop_resources import load_desktop
    m=api(); alpha=supplied(client)
    second=scratch/'second'; second.mkdir(); other=factory.__wrapped__(second)
    beta=supplied(other)
    for name in ('descriptor','policy','binding','access_scope'): beta[name]['client_id']='beta'
    for name in ('descriptor','policy'): beta[name]['repository']='demo/beta'
    beta['repository_url']='https://github.com/demo/beta.git'
    beta['binding']['state_dir']=str(second/'state/beta/checkout')
    beta['guided_request']['development']['client_id']='beta'
    beta['guided_request']['development']['business_rules']=['Regla sintética beta']
    beta['guided_request']['tool_binding']['client_id']='beta'
    other['policy'].write_bytes(canonical(beta['policy']))
    from harness_core.onboarding_plan import sha
    beta['binding']['policy_sha256']=sha(other['policy'].read_bytes())
    beta['access_scope']['policy_sha256']=beta['binding']['policy_sha256']
    other['binding'].write_bytes(canonical(beta['binding']))
    (other['target']/'.harness/client.yaml').write_bytes(canonical(beta['descriptor']))
    subprocess.run(['git','-C',str(other['target']),'remote','set-url','origin',beta['repository_url']],capture_output=True,check=True)
    (other['target']/'.codex/agents').mkdir(parents=True)
    custom='[agents]\nmax_concurrent_threads_per_session = 2\n'
    (other['target']/'.codex/config.toml').write_text(custom,encoding='utf-8')
    personal='name = "personal"\ndescription = "Propio"\ndeveloper_instructions = "Conservar"\n'
    (other['target']/'.codex/agents/personal.toml').write_text(personal,encoding='utf-8')
    (other['target']/'AGENTS.md').write_text('Instrucciones propias beta\n',encoding='utf-8')
    catalog=load_desktop()
    profiles={r.id:dict(model='test-model',effort='medium') for r in catalog.roles}
    beta['guided_request']['catalog']=activate_profiles(catalog,profiles,{'test-model':['medium']}).model_dump()
    beta['guided_request']['development']['roles']=list(profiles)
    for data,folder_,label in ((alpha,scratch,'alpha'),(beta,second,'beta')):
        path=folder_/('parent-'+label+'.json')
        preview,code=m.preview(data,probe_fn=ready,plan_out=path); assert code==0
        output,code=m.apply(path,preview['plan']['plan_sha256'],probe_fn=ready); assert code==0
        assert output['report']['client_id']==label
    assert (other['target']/'.codex/config.toml').read_text(encoding='utf-8')==custom
    assert (other['target']/'.codex/agents/personal.toml').read_text(encoding='utf-8')==personal
    assert (other['target']/'AGENTS.md').read_text(encoding='utf-8').startswith('Instrucciones propias beta\n')
    assert len(list((other['target']/'.codex/agents').glob('harness-*.toml')))==8
    assert 'beta' not in (client['target']/'.harness/context.md').read_text(encoding='utf-8')
