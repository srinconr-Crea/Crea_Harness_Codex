"""Real SQLite, prepared synthetic clients and Git; no Desktop certification."""
import json
import subprocess
import sqlite3

import pytest

from harness_core.configuration import ConfigError
from harness_local import guided_onboarding as guided
from test_guided_onboarding import setup, ready


def git(target, *args):
    return subprocess.run(['git', '-C', str(target), *args], check=True, capture_output=True).stdout


@pytest.fixture
def hu(client):
    from harness_local.hu import HuService
    from harness_local.desktop_resources import load_desktop
    from harness_core.desktop import activate_profiles
    from harness_core.guided import QuestionnaireDraft
    draft, plan, _ = setup(client)
    raw=draft.model_dump()
    roles=['principal','developer','tester','auditor']
    profiles={role:dict(model='test-model',effort='medium') for role in roles}
    raw['answers']['catalog']['value']=activate_profiles(load_desktop(),profiles,{'test-model':['medium']}).model_dump()
    raw['answers']['development']['value']['roles']=roles
    draft=QuestionnaireDraft.model_validate(raw)
    guided.preview(draft, probe_fn=ready, plan_out=plan)
    guided.apply(plan, stage='prepare', probe_fn=ready)
    git(client['target'], 'config', 'core.autocrlf', 'false')
    git(client['target'], 'add', '.')
    git(client['target'], '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-m', 'prepared')
    service = HuService(client['target'], client['policy'], client['binding'])
    service.run('start', 'HU1', 'start1', dict(schema_version=1, writer_actor='developer', onboarding_plan=str(plan), simulation=True))
    return service, client, plan


def plan(service, op='plan1', **updates):
    data = dict(schema_version=1, criteria=['Suma decimal por cliente'],
        paths=['src/total.py', 'tests/test_total.py'], operations=['create', 'modify', 'delete'],
        tests=['T16'], required_capabilities=[], max_delegations=2, allow_worktrees=False,
        sources={'story': 'user'}, decisions=['HU pequeña: principal y revisión independiente'])
    data.update(updates)
    return service.run('plan', 'HU1', op, data)


def approved(service):
    p = plan(service)['run']['plan']
    return service.run('approve', 'HU1', 'approve1', dict(schema_version=1, actor='operator',
        confirmed=True, plan_sha256=p['plan_sha256'], client_id='alpha', checkout_id='checkout', attempt=1, revision=1))


def candidate(service, client):
    (client['target'] / 'src').mkdir(exist_ok=True)
    (client['target'] / 'src/total.py').write_text('def total(xs): return sum(xs)\n')
    return service.run('candidate', 'HU1', 'candidate1', {'schema_version': 1})['run']['candidate']


def test_preparation_dependency_and_invalid_identity(client):
    from harness_local.hu import HuService
    service = HuService(client['target'], client['policy'], client['binding'])
    with pytest.raises(ConfigError):
        service.run('start', 'HU1', 's', dict(schema_version=1, writer_actor='developer', onboarding_plan=str(client['target']/'absent'), simulation=False))
    assert not service.state.exists()


def test_revision_bound_approval_and_idempotency(hu):
    service, client, _ = hu
    first = approved(service)
    assert first['run']['state'] == 'approved'
    repeated = service.run('approve', 'HU1', 'approve1', dict(schema_version=1, actor='operator', confirmed=True,
        plan_sha256=first['run']['plan']['plan_sha256'], client_id='alpha', checkout_id='checkout', attempt=1, revision=1))
    assert repeated['idempotent']
    revised = plan(service, 'plan2', criteria=['Incluir impuestos'])
    assert revised['run']['state'] == 'planned' and revised['run']['approval'] is None
    result = service.run('transition', 'HU1', 'implement', dict(schema_version=1, state='implementing'))
    assert result['status'] == 'blocked' and result['run']['blocked_reason'] == 'approval_required'
    assert service.run('status', 'HU1')['history'][-1]['status'] == 'blocked'


@pytest.mark.parametrize('updates', [dict(client_id='beta'), dict(checkout_id='other'), dict(attempt=2),
    dict(revision=2), dict(plan_sha256='0'*64), dict(confirmed=False)])
def test_wrong_approval_rejected(hu, updates):
    service, _, _ = hu
    p = plan(service)['run']['plan']
    data = dict(schema_version=1, actor='operator', confirmed=True, plan_sha256=p['plan_sha256'],
        client_id='alpha', checkout_id='checkout', attempt=1, revision=1)
    data.update(updates)
    assert service.run('approve', 'HU1', 'bad', data)['status'] == 'blocked'


def test_candidate_edited_and_scope_bypass(hu):
    service, client, _ = hu
    approved(service)
    c = candidate(service, client)
    assert c['entries'][0]['operation'] == 'create'
    (client['target'] / 'outside.py').write_text('unapproved')
    result = service.run('candidate', 'HU1', 'outside', {'schema_version': 1})
    assert result['status'] == 'blocked' and result['run']['blocked_reason'] == 'scope_denied'
    (client['target'] / 'outside.py').unlink()
    c=service.run('candidate','HU1','recaptured',{'schema_version':1})['run']['candidate']
    service.run('transition', 'HU1', 'validate', dict(schema_version=1, state='validating'))
    e = dict(schema_version=1, id='T16', candidate_sha256=c['candidate_sha256'], status='passed',
        simulated=True, actor='tester', kind='test', evidence_ref='fixture-1')
    service.run('evidence', 'HU1', 'test1', e)
    (client['target'] / 'src/total.py').write_text('changed')
    result = service.run('transition', 'HU1', 'review', dict(schema_version=1, state='reviewing'))
    assert result['status'] == 'blocked' and result['run']['blocked_reason'] == 'candidate_changed'
    assert result['run']['evidence'] == []


def test_synthetic_ready_has_no_publication_authority(hu):
    service, client, _ = hu
    approved(service)
    c = candidate(service, client)
    service.run('transition', 'HU1', 'validate', dict(schema_version=1, state='validating'))
    for status in ('not_run', 'blocked', 'failed'):
        service.run('evidence', 'HU1', status, dict(schema_version=1, id='T16', candidate_sha256=c['candidate_sha256'],
            status=status, simulated=True, actor='tester', kind='test', evidence_ref='fixture'))
        assert service.run('transition', 'HU1', 'review-'+status, dict(schema_version=1, state='reviewing'))['status'] == 'blocked'
    service.run('evidence', 'HU1', 'pass', dict(schema_version=1, id='T16', candidate_sha256=c['candidate_sha256'],
        status='passed', simulated=True, actor='tester', kind='test', evidence_ref='fixture'))
    assert service.run('transition', 'HU1', 'review', dict(schema_version=1, state='reviewing'))['run']['state'] == 'reviewing'
    service.run('evidence', 'HU1', 'audit', dict(schema_version=1, id='audit', candidate_sha256=c['candidate_sha256'],
        status='passed', simulated=True, actor='independent-reviewer', kind='review', evidence_ref='fixture-review'))
    result = service.run('transition', 'HU1', 'ready', dict(schema_version=1, state='ready_to_publish'))
    assert result['run']['state'] == 'ready_to_publish' and result['status'] == 'partial'
    assert result['publication_allowed'] is False
    assert service.run('transition', 'HU1', 'publish', dict(schema_version=1, state='published'))['status'] == 'blocked'


def test_real_run_rejects_simulated_evidence(hu):
    service, client, onboarding = hu
    service.run('start', 'REAL', 's', dict(schema_version=1, writer_actor='developer', onboarding_plan=str(onboarding), simulation=False))
    p = service.run('plan', 'REAL', 'p', dict(schema_version=1, criteria=['x'], paths=['src/total.py'],
        operations=['create'], tests=['T16']))['run']['plan']
    service.run('approve', 'REAL', 'a', dict(schema_version=1, actor='operator', confirmed=True, client_id='alpha',
        checkout_id='checkout', attempt=1, revision=1, plan_sha256=p['plan_sha256']))
    (client['target'] / 'src').mkdir()
    (client['target'] / 'src/total.py').write_text('x')
    c = service.run('candidate', 'REAL', 'c', dict(schema_version=1))['run']['candidate']
    service.run('transition', 'REAL', 'v', dict(schema_version=1, state='validating'))
    service.run('evidence', 'REAL', 'e', dict(schema_version=1, id='T16', candidate_sha256=c['candidate_sha256'],
        status='passed', simulated=True, actor='tester', kind='test', evidence_ref='fixture'))
    assert service.run('transition', 'REAL', 'r', dict(schema_version=1, state='reviewing'))['status'] == 'blocked'


def test_limits_writer_and_infrastructure_recovery(hu):
    service, _, _ = hu
    approved(service)
    payload = dict(schema_version=1, role='developer', actor='writer', write_paths=['src/total.py'],
        isolation='checkout', delegation_depth=0)
    assert service.run('assign', 'HU1', 'writer', payload)['status'] != 'blocked'
    assert service.run('assign', 'HU1', 'writer2', {**payload, 'actor':'other'})['status'] == 'blocked'
    before = service.run('status', 'HU1')['run']['corrections']
    blocked = service.run('block', 'HU1', 'infra', dict(schema_version=1, reason='tool_unavailable'))
    assert blocked['run']['corrections'] == before
    for index in range(2):
        assert service.run('correct', 'HU1', 'fix'+str(index), dict(schema_version=1))['status'] != 'blocked'
    assert service.run('correct', 'HU1', 'third', dict(schema_version=1))['status'] == 'blocked'
    resumed = service.run('resume', 'HU1', 'resume', dict(schema_version=1))
    assert resumed['run']['corrections'] == 2
    assert service.run('resume', 'HU1', 'resume', dict(schema_version=1))['idempotent']


def test_unknown_schema_and_secret_redacted(hu):
    service, _, _ = hu
    for data in ({'schema_version':2}, {'schema_version':1, 'unknown':'x'},
                 {'schema_version':1, 'reason':'token=private'}):
        with pytest.raises(ConfigError) as error:
            service.run('block', 'HU1', 'bad', data)
        assert 'private' not in str(error.value)


def test_committed_transaction_survives_process_loss(hu, monkeypatch):
    from harness_local import hu as module
    service, _, _ = hu
    approved(service)
    def crash(point):
        if point == 'after_commit': raise RuntimeError('process lost')
    monkeypatch.setattr(module, 'checkpoint', crash)
    with pytest.raises(RuntimeError):
        service.run('block', 'HU1', 'loss', dict(schema_version=1, reason='tool_unavailable'))
    monkeypatch.setattr(module, 'checkpoint', lambda point: None)
    repeated = service.run('block', 'HU1', 'loss', dict(schema_version=1, reason='tool_unavailable'))
    assert repeated['idempotent']
    history = service.run('status', 'HU1')['history']
    assert sum(h['operation_id']=='loss' for h in history) == 1
    assert json.loads((service.state/'hu-artifacts/HU1.json').read_text())['run']['blocked_reason'] == 'tool_unavailable'


def test_modified_deleted_and_new_files_in_candidate(hu):
    service, client, _ = hu
    root=client['target']
    (root/'src').mkdir()
    (root/'src/old.py').write_text('old\n')
    (root/'src/gone.py').write_text('gone\n')
    git(root,'add','.')
    git(root,'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','baseline')
    # Separate attempt with the new immutable base.
    service.run('start','DIFF','s',dict(schema_version=1,writer_actor='developer', onboarding_plan=str(hu[2]),simulation=True))
    p=service.run('plan','DIFF','p',dict(schema_version=1,criteria=['x'],paths=['src'],
        operations=['create','modify','delete'],tests=['T16']))['run']['plan']
    service.run('approve','DIFF','a',dict(schema_version=1,actor='operator',confirmed=True,client_id='alpha',
        checkout_id='checkout',attempt=1,revision=1,plan_sha256=p['plan_sha256']))
    (root/'src/old.py').write_text('changed\n')
    (root/'src/gone.py').unlink()
    (root/'src/new.py').write_text('new\n')
    entries=service.run('candidate','DIFF','c',dict(schema_version=1))['run']['candidate']['entries']
    assert {e['path']:e['operation'] for e in entries} == {'src/old.py':'modify','src/gone.py':'delete','src/new.py':'create'}


def test_context_change_invalidates_and_requires_replanning(hu):
    service, client, _ = hu
    approved(service)
    context=client['target']/'.harness/context.md'
    context.write_text(context.read_text(encoding='utf-8')+'\nNueva regla\n',encoding='utf-8')
    result=service.run('transition','HU1','i',dict(schema_version=1,state='implementing'))
    assert result['run']['state']=='planned' and result['run']['approval'] is None
    assert result['run']['blocked_reason']=='context_changed'


def test_capability_missing_and_independent_review_required(hu):
    service, client, _ = hu
    p=plan(service,required_capabilities=['isolation'])['run']['plan']
    service.run('approve','HU1','a',dict(schema_version=1,actor='operator',confirmed=True,client_id='alpha',
        checkout_id='checkout',attempt=1,revision=1,plan_sha256=p['plan_sha256']))
    c=candidate(service,client)
    result=service.run('transition','HU1','v',dict(schema_version=1,state='validating'))
    assert result['run']['blocked_reason']=='capability_required'


def test_writer_collision_across_stories_and_delegation_limit(hu):
    service, _, onboarding=hu
    approved(service)
    payload=dict(schema_version=1,role='developer',actor='writer',write_paths=['src/total.py'],isolation='checkout',delegation_depth=0)
    service.run('assign','HU1','w',payload)
    service.run('start','HU2','s',dict(schema_version=1,writer_actor='developer', onboarding_plan=str(onboarding),simulation=True))
    p=service.run('plan','HU2','p',dict(schema_version=1,criteria=['x'],paths=['src'],operations=['create'],tests=['T16']))['run']['plan']
    service.run('approve','HU2','a',dict(schema_version=1,actor='operator',confirmed=True,client_id='alpha',checkout_id='checkout',
        attempt=1,revision=1,plan_sha256=p['plan_sha256']))
    assert service.run('assign','HU2','w',{**payload,'actor':'other'})['run']['blocked_reason']=='writer_collision'
    review={**payload,'role':'auditor','actor':'reviewer','write_paths':[]}
    assert service.run('assign','HU1','r',review)['status']=='ready'
    assert service.run('assign','HU1','r2',{**review,'actor':'reviewer2'})['run']['blocked_reason']=='delegation_limit'


def test_rollback_before_commit_and_unknown_database_version(hu, monkeypatch):
    from harness_local import hu as module
    service,_,_=hu
    original=service.run('status','HU1')['history']
    def crash(point):
        if point=='before_commit': raise RuntimeError('loss')
    monkeypatch.setattr(module,'checkpoint',crash)
    with pytest.raises(RuntimeError): service.run('block','HU1','loss',dict(schema_version=1,reason='tool_unavailable'))
    assert service.run('status','HU1')['history']==original
    with sqlite3.connect(service.state/'hu.sqlite3') as db: db.execute('PRAGMA user_version=99')
    with pytest.raises(ConfigError,match='hu_state_version'): service.run('status','HU1')


def test_allowed_worktree_creation_and_resume_without_duplicate(hu):
    service,client,_=hu
    p=plan(service,allow_worktrees=True)['run']['plan']
    service.run('approve','HU1','a',dict(schema_version=1,actor='operator',confirmed=True,client_id='alpha',checkout_id='checkout',
        attempt=1,revision=1,plan_sha256=p['plan_sha256']))
    path=client['target'].parent/'isolated'
    data=dict(schema_version=1,path=str(path),branch='isolated-hu',confirmed=True)
    created=service.run('worktree','HU1','wt',data)
    assert created['status']=='ready' and (path/'.git').is_file()
    assert service.run('worktree','HU1','wt',data)['idempotent']
    assert len(service.run('status','HU1')['run']['worktrees'])==1


def test_worktree_denied_has_no_effect(hu):
    service,client,_=hu
    approved(service)
    path=client['target'].parent/'denied'
    result=service.run('worktree','HU1','wt',dict(schema_version=1,path=str(path),branch='denied-hu',confirmed=True))
    assert result['run']['blocked_reason']=='worktree_denied' and not path.exists()


def test_crlf_baseline_and_external_byte_edit(hu):
    service,client,onboarding=hu
    root=client['target']
    git(root,'config','core.autocrlf','true')
    (root/'existing.py').write_bytes(b'one\r\ntwo\r\n')
    git(root,'add','existing.py')
    git(root,'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','crlf')
    service.run('start','CRLF','s',dict(schema_version=1,writer_actor='developer', onboarding_plan=str(onboarding),simulation=True))
    p=service.run('plan','CRLF','p',dict(schema_version=1,criteria=['x'],paths=['src'],operations=['create'],tests=['T16']))['run']['plan']
    service.run('approve','CRLF','a',dict(schema_version=1,actor='operator',confirmed=True,client_id='alpha',checkout_id='checkout',
        attempt=1,revision=1,plan_sha256=p['plan_sha256']))
    assert service.run('candidate','CRLF','c',dict(schema_version=1))['status']=='ready'
    (root/'existing.py').write_bytes(b'one\ntwo\n')
    assert service.run('candidate','CRLF','edited',dict(schema_version=1))['run']['blocked_reason']=='scope_denied'


def test_worktree_crash_reconciliation(hu,monkeypatch):
    from harness_local import hu as module
    service,client,_=hu
    p=plan(service,allow_worktrees=True)['run']['plan']
    service.run('approve','HU1','a',dict(schema_version=1,actor='operator',confirmed=True,client_id='alpha',checkout_id='checkout',
        attempt=1,revision=1,plan_sha256=p['plan_sha256']))
    path=client['target'].parent/'interrupted'
    def crash(point):
        if point=='worktree_created': raise RuntimeError('loss')
    monkeypatch.setattr(module,'checkpoint',crash)
    with pytest.raises(RuntimeError):
        service.run('worktree','HU1','wt',dict(schema_version=1,path=str(path),branch='interrupted-hu',confirmed=True))
    monkeypatch.setattr(module,'checkpoint',lambda point:None)
    resumed=service.run('resume','HU1','resume',dict(schema_version=1))
    assert resumed['status']=='ready' and len(resumed['run']['worktrees'])==1
    assert service.run('resume','HU1','resume',dict(schema_version=1))['idempotent']


def test_new_attempt_requires_failed_state(hu):
    service,_,_=hu
    approved(service)
    assert service.run('attempt','HU1','early',dict(schema_version=1))['status']=='blocked'
    service.run('transition','HU1','fail',dict(schema_version=1,state='failed'))
    result=service.run('attempt','HU1','retry',dict(schema_version=1))
    assert result['run']['attempt']==2 and result['run']['state']=='draft'
    assert result['run']['approval'] is None and result['run']['corrections']==0


def test_real_process_loss_rolls_back_without_success(hu):
    import sys
    from pathlib import Path
    service,_,_=hu
    script=service.target.parent/'crash.py'
    script.write_text('import sys,os\nsys.path.insert(0,'+repr(str(Path('src').resolve()))+')\n'
        'from harness_local.hu import HuService\nfrom harness_local import hu\n'
        'hu.checkpoint=lambda point: os._exit(23) if point=="before_commit" else None\n'
        'HuService('+','.join(repr(str(p)) for p in (service.target,service.policy_path,service.binding_path))+')'
        '.run("block","HU1","lost",dict(schema_version=1,reason="tool_unavailable"))\n')
    process=subprocess.run([sys.executable,str(script)],capture_output=True)
    assert process.returncode==23
    result=service.run('resume','HU1','r',dict(schema_version=1))
    assert all(h['operation_id']!='lost' for h in service.run('status','HU1')['history'])
    assert result['run']['state']=='draft'


def test_oversized_file_cannot_hide_tail_edits(hu):
    service,client,_=hu
    approved(service)
    (client['target']/'src').mkdir()
    (client['target']/'src/total.py').write_bytes(b'x'*(2*1024*1024+1))
    result=service.run('candidate','HU1','large',dict(schema_version=1))
    assert result['status']=='blocked' and result['run']['candidate'] is None


def test_same_test_actor_cannot_self_review_without_assignment(hu):
    service,client,_=hu
    approved(service)
    c=candidate(service,client)
    service.run('transition','HU1','v',dict(schema_version=1,state='validating'))
    for kind,id in [('test','T16'),('review','audit')]:
        service.run('evidence','HU1',kind,dict(schema_version=1,id=id,candidate_sha256=c['candidate_sha256'],
            status='passed',simulated=True,actor='developer',kind=kind,evidence_ref='fixture'))
    service.run('transition','HU1','r',dict(schema_version=1,state='reviewing'))
    result=service.run('transition','HU1','ready',dict(schema_version=1,state='ready_to_publish'))
    assert result['run']['blocked_reason']=='independent_review_required'


def test_idempotent_gate_revalidates_changed_candidate(hu):
    service,client,_=hu
    approved(service)
    candidate(service,client)
    assert service.run('resume','HU1','r',dict(schema_version=1))['status']=='ready'
    (client['target']/'src/total.py').write_text('changed')
    result=service.run('resume','HU1','r',dict(schema_version=1))
    assert result['status']=='blocked' and result['run']['candidate'] is None


def test_index_cannot_hide_out_of_scope_diff(hu):
    service,client,onboarding=hu
    root=client['target']
    (root/'outside.py').write_bytes(b'before\n')
    git(root,'add','outside.py')
    git(root,'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','outside baseline')
    service.run('start','INDEX','s',dict(schema_version=1,writer_actor='developer', onboarding_plan=str(onboarding),simulation=True))
    p=service.run('plan','INDEX','p',dict(schema_version=1,criteria=['x'],paths=['src'],operations=['create'],tests=['T16']))['run']['plan']
    service.run('approve','INDEX','a',dict(schema_version=1,actor='operator',confirmed=True,client_id='alpha',checkout_id='checkout',
        attempt=1,revision=1,plan_sha256=p['plan_sha256']))
    (root/'outside.py').write_bytes(b'after\n')
    git(root,'add','outside.py')
    (root/'outside.py').write_bytes(b'before\n')
    result=service.run('candidate','INDEX','c',dict(schema_version=1))
    assert result['status']=='blocked' and result['run']['blocked_reason']=='scope_denied'


def test_reused_adapter_reloads_policy_before_replanning(hu):
    from harness_core.onboarding_plan import sha
    service,client,_=hu
    approved(service)
    policy=json.loads(client['policy'].read_text())
    policy['denied_paths'].append('src/')
    client['policy'].write_text(json.dumps(policy))
    binding=json.loads(client['binding'].read_text())
    binding['policy_sha256']=sha(client['policy'].read_bytes())
    client['binding'].write_text(json.dumps(binding))
    assert plan(service,'replan')['run']['blocked_reason']=='scope_denied'


def test_principal_writer_cannot_review_with_different_tester(hu):
    service,client,_=hu
    approved(service)
    c=candidate(service,client)
    service.run('transition','HU1','v',dict(schema_version=1,state='validating'))
    service.run('evidence','HU1','t',dict(schema_version=1,id='T16',candidate_sha256=c['candidate_sha256'],
        status='passed',simulated=True,actor='tester',kind='test',evidence_ref='fixture'))
    service.run('transition','HU1','r',dict(schema_version=1,state='reviewing'))
    service.run('evidence','HU1','a',dict(schema_version=1,id='audit',candidate_sha256=c['candidate_sha256'],
        status='passed',simulated=True,actor='developer',kind='review',evidence_ref='fixture'))
    assert service.run('transition','HU1','ready',dict(schema_version=1,state='ready_to_publish'))['run']['blocked_reason']=='independent_review_required'


def test_two_clients_isolated_hu_state(hu,scratch):
    from harness_local.hu import HuService
    from harness_core.guided import QuestionnaireDraft
    from test_guided_onboarding import snapshot
    service,client,onboarding=hu
    approved(service)
    original=snapshot(service.state)
    beta=scratch/'beta'; beta.mkdir()
    git(beta,'init','--initial-branch=develop')
    git(beta,'remote','add','origin','https://github.com/demo/beta.git')
    policy=json.loads(client['policy'].read_text()); policy.update(client_id='beta',repository='demo/beta')
    bp=scratch/'beta-policy.json'; bp.write_text(json.dumps(policy))
    frozen=json.loads(onboarding.read_text(encoding='utf-8'))['provenance']
    values=dict(target_path=str(beta),policy_path=str(bp),binding_path=str(scratch/'beta-binding.json'),binding_mode='proposed',
        state_dir=str(scratch/'state/beta/other'),repository='demo/beta',base_branch='develop')
    for key,value in values.items(): frozen['answers'][key]=dict(value=value,status='known',source='user',confirmed=True)
    frozen['answers']['development']['value'].update(client_id='beta',business_rules=['Only beta'])
    frozen['answers']['tool_binding']['value'].update(client_id='beta',checkout_id='other')
    bplan=scratch/'beta-plan.json'
    guided.preview(QuestionnaireDraft.model_validate(frozen),probe_fn=ready,plan_out=bplan)
    guided.apply(bplan,stage='prepare',probe_fn=ready)
    git(beta,'config','core.autocrlf','false'); git(beta,'add','.')
    git(beta,'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','beta prepared')
    bservice=HuService(beta,bp,values['binding_path'])
    bservice.run('start','HU1','s',dict(schema_version=1,writer_actor='beta-writer',onboarding_plan=str(bplan),simulation=True))
    assert bservice.run('status','HU1')['run']['client_id']=='beta'
    assert snapshot(service.state)==original
    with pytest.raises(ConfigError): bservice.run('start','foreign','f',dict(schema_version=1,writer_actor='writer',onboarding_plan=str(onboarding)))
    assert 'Only beta' not in json.dumps(service.run('status','HU1'))


def test_inactive_role_is_blocked(hu):
    service,_,_=hu
    approved(service)
    result=service.run('assign','HU1','inactive',dict(schema_version=1,role='verifier',actor='verifier',
        write_paths=[],isolation='checkout',delegation_depth=0))
    assert result['run']['blocked_reason']=='role_inactive'


def test_handoff_and_positive_required_capability(hu):
    service,client,_=hu
    p=plan(service,required_capabilities=['isolation'])['run']['plan']
    service.run('approve','HU1','a',dict(schema_version=1,actor='operator',confirmed=True,client_id='alpha',checkout_id='checkout',
        attempt=1,revision=1,plan_sha256=p['plan_sha256']))
    c=candidate(service,client)
    service.run('evidence','HU1','cap',dict(schema_version=1,id='isolation',candidate_sha256=c['candidate_sha256'],
        status='passed',simulated=False,actor='operator',kind='capability',evidence_ref='synthetic-contract-control'))
    assert service.run('transition','HU1','v',dict(schema_version=1,state='validating'))['status']=='ready'
    handoff=dict(schema_version=1,role='developer',actor='developer',plan_sha256=p['plan_sha256'],candidate_sha256=c['candidate_sha256'],
        sources={'story':'user'},decisions=['HU pequeña sin fanout'],findings=[],status='completed')
    assert service.run('handoff','HU1','h',handoff)['run']['handoffs'][0]['sources']=={'story':'user'}
    assert service.run('handoff','HU1','stale',{**handoff,'plan_sha256':'0'*64})['status']=='blocked'


def test_old_plan_cannot_be_approved_after_context_drift(hu):
    service,client,_=hu
    old=approved(service)['run']['approval']
    context=client['target']/'.harness/context.md'
    context.write_text(context.read_text(encoding='utf-8')+'\nChanged rule\n',encoding='utf-8')
    service.run('transition','HU1','drift',dict(schema_version=1,state='implementing'))
    old.pop('approved_at')
    result=service.run('approve','HU1','stale-approval',old)
    assert result['status']=='blocked' and result['run']['approval'] is None and result['run']['state']=='planned'


def test_cancelled_attempt_cannot_reopen_on_replayed_operation(hu):
    service,client,_=hu
    approved(service)
    candidate(service,client)
    service.run('transition','HU1','cancel',dict(schema_version=1,state='cancelled'))
    (client['target']/'src/total.py').write_text('changed')
    context=client['target']/'.harness/context.md'
    context.write_text(context.read_text(encoding='utf-8')+'\nChanged after cancellation\n',encoding='utf-8')
    result=service.run('transition','HU1','cancel',dict(schema_version=1,state='cancelled'))
    assert result['run']['state']=='cancelled'
    assert service.run('transition','HU1','reopen',dict(schema_version=1,state='implementing'))['status']=='blocked'


def test_unassigned_principal_paths_reserve_parent_scope(hu):
    service,_,onboarding=hu
    approved(service)
    service.run('start','HU2','s',dict(schema_version=1,writer_actor='other',onboarding_plan=str(onboarding),simulation=True))
    p=service.run('plan','HU2','p',dict(schema_version=1,criteria=['x'],paths=['src'],operations=['create'],tests=['T16']))['run']['plan']
    service.run('approve','HU2','a',dict(schema_version=1,actor='operator',confirmed=True,client_id='alpha',checkout_id='checkout',
        attempt=1,revision=1,plan_sha256=p['plan_sha256']))
    result=service.run('assign','HU2','w',dict(schema_version=1,role='developer',actor='other',write_paths=['src'],isolation='checkout',delegation_depth=0))
    assert result['run']['blocked_reason']=='writer_collision'
