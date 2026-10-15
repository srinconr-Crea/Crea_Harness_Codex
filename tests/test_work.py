import importlib

import pytest

from harness_core.configuration import ConfigError
from test_hu_lifecycle import hu
from test_setup_hu_scope import attach


def api():
    assert importlib.util.find_spec('harness_local.work'), 'work facade missing'
    return importlib.import_module('harness_local.work')


def request(plan):
    return dict(schema_version=1,story_id='HU2',story='Sumar valores sintéticos',
        onboarding_plan=str(plan),writer_actor='developer',criteria=['Suma exacta'],
        paths=['src/total.py'],operations=['create','modify'],tests=['T16'],
        mode='supervised_single_agent',available_models={'test-model':['medium']})


def test_work_preview_start_and_resume_keep_approval(hu):
    service,client,plan=hu
    attach(service,client)
    from harness_local.activity_ledger import ActivityLedger
    ledger=ActivityLedger(service.config['binding']); ledger.initialize()
    work=api().WorkService(client['target'],client['policy'],client['binding'])
    before=ledger.path.read_bytes()
    preview=work.preview(request(plan))
    assert preview['status']=='ready'
    assert ledger.path.read_bytes()==before
    result=work.start(request(plan),preview['plan']['plan_sha256'])
    assert result['run']['state']=='approved'
    approval=result['run']['approval']
    assert work.start(request(plan),preview['plan']['plan_sha256'])['idempotent']
    resumed=api().WorkService(client['target'],client['policy'],client['binding']).resume('HU2','resume-1')
    assert resumed['run']['approval']==approval
    assert not resumed['publication_allowed']


def test_work_missing_decisions_and_native_capacity_are_explicit(hu):
    service,client,plan=hu
    attach(service,client)
    work=api().WorkService(client['target'],client['policy'],client['binding'])
    raw=request(plan); raw.pop('criteria')
    assert 'criteria' in work.preview(raw)['questions']
    raw=request(plan); raw['mode']='native'; raw['delegation_available']=False
    assert work.preview(raw)['reason']=='native_delegation_unavailable'
    raw=request(plan); raw['available_models']={}
    assert work.preview(raw)['reason']=='model_unavailable'
    raw=request(plan); raw['requires_independence']=True
    assert work.preview(raw)['reason']=='native_isolation_unavailable'


def test_work_rejects_stale_review_before_creating_hu(hu):
    service,client,plan=hu
    attach(service,client)
    work=api().WorkService(client['target'],client['policy'],client['binding'])
    raw=request(plan)
    with pytest.raises(ConfigError,match='plan_stale'):
        work.start(raw,'0'*64)
    with pytest.raises(ConfigError,match='hu_not_found'):
        work.status('HU2')


def test_status_uses_read_only_database_without_lock_or_migration(hu,monkeypatch):
    service,client,plan=hu
    import harness_local.hu as module
    def lock(*args,**kwargs):
        pytest.fail('status attempted a checkout write lock')
    monkeypatch.setattr(module,'CheckoutLock',lock)
    assert service.run('status','HU1')['run']['state']=='draft'


def test_work_replans_existing_hu_with_reviewed_next_revision(hu):
    service,client,plan=hu
    attach(service,client)
    from harness_local.activity_ledger import ActivityLedger
    ActivityLedger(service.config['binding']).initialize()
    work=api().WorkService(client['target'],client['policy'],client['binding'])
    raw=request(plan); preview=work.preview(raw)
    work.start(raw,preview['plan']['plan_sha256'])
    raw['criteria']=['Suma exacta, incluyendo vacío']
    revised=work.preview(raw)
    assert revised['plan']['revision']==2
    result=work.start(raw,revised['plan']['plan_sha256'])
    assert result['run']['state']=='approved'
    assert result['run']['approval']['revision']==2
    assert work.preview(raw)['plan']['plan_sha256']==revised['plan']['plan_sha256']


def test_work_status_surfaces_unreconciled_activity_without_claiming_success(hu):
    service,client,plan=hu
    from harness_local.activity_ledger import ActivityLedger
    ledger=ActivityLedger(service.config['binding']); ledger.initialize()
    with pytest.raises(KeyboardInterrupt):
        with ledger.operation('lost-adapter',scope='hu',hu_id='HU1',attempt=1): raise KeyboardInterrupt()
    status=api().WorkService(client['target'],client['policy'],client['binding']).status('HU1')
    assert status['activity_pending_operations']==1
    assert status['next_action']=='reconcile_pending'


def test_work_start_after_explicit_new_attempt_does_not_replay_old_plan(hu):
    service,client,plan=hu
    attach(service,client)
    from harness_local.activity_ledger import ActivityLedger
    ActivityLedger(service.config['binding']).initialize()
    work=api().WorkService(client['target'],client['policy'],client['binding'])
    raw=request(plan); preview=work.preview(raw)
    work.start(raw,preview['plan']['plan_sha256'])
    work.hu.run('transition','HU2','failed',dict(schema_version=1,state='failed'))
    work.hu.run('attempt','HU2','new-attempt',dict(schema_version=1))
    preview=work.preview(raw)
    result=work.start(raw,preview['plan']['plan_sha256'])
    assert result['run']['attempt']==2 and result['run']['state']=='approved'
    assert result['run']['approval']['attempt']==2


def test_work_unprepared_client_never_creates_state(client):
    from pathlib import Path
    import json
    work=api().WorkService(client['target'],client['policy'],client['binding'])
    with pytest.raises(ConfigError,match='hu_preparation_required'):
        work.preview(request(client['binding']))
    assert not Path(json.loads(client['binding'].read_text())['state_dir']).exists()


def test_work_base_change_after_preview_requires_new_review(hu):
    from test_hu_lifecycle import git
    service,client,plan=hu
    attach(service,client)
    from harness_local.activity_ledger import ActivityLedger
    ActivityLedger(service.config['binding']).initialize()
    work=api().WorkService(client['target'],client['policy'],client['binding'])
    raw=request(plan); preview=work.preview(raw)
    git(client['target'],'-c','user.name=Test','-c','user.email=test@example.invalid','commit','--allow-empty','-m','New baseline')
    with pytest.raises(ConfigError,match='plan_stale'):
        work.start(raw,preview['plan']['plan_sha256'])


def test_existing_work_rejects_changed_base_before_offering_new_approval(hu):
    from test_hu_lifecycle import git
    service,client,plan=hu
    attach(service,client)
    from harness_local.activity_ledger import ActivityLedger
    ledger=ActivityLedger(service.config['binding']); ledger.initialize()
    work=api().WorkService(client['target'],client['policy'],client['binding'])
    raw=request(plan); preview=work.preview(raw)
    started=work.start(raw,preview['plan']['plan_sha256'])
    git(client['target'],'-c','user.name=Test','-c','user.email=test@example.invalid','commit','--allow-empty','-m','New baseline')
    before=ledger.path.read_bytes()
    changed=work.preview(raw)
    assert changed['status']=='blocked' and changed['reason']=='base_changed'
    assert work.start(raw,preview['plan']['plan_sha256'])['reason']=='base_changed'
    assert ledger.path.read_bytes()==before
    assert work.hu.run('status','HU2')['run']['approval']==started['run']['approval']
