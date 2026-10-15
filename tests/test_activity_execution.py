import importlib

import pytest

from harness_core.configuration import ConfigError
from harness_local.activity_ledger import ActivityLedger
from test_activity_ledger import selected


def api():
    assert importlib.util.find_spec('harness_local.activity_execution'), 'explicit activity execution missing'
    return importlib.import_module('harness_local.activity_execution')


def context(client):
    return dict(schema_version=1,target_path=str(client['target']),policy_path=str(client['policy']),
        binding_path=str(client['binding']),operation_id='validation1')


def test_adapter_records_result_and_prevents_blind_replay(client):
    ledger=ActivityLedger(selected(client)); ledger.initialize()
    module=api()
    result=module.run(context(client),'validate_static',lambda:({'status':'failed'},1))
    assert result[1]==1 and ledger.report()['failed_operations']==1
    with pytest.raises(ConfigError,match='ledger_operation_completed'):
        module.run(context(client),'validate_static',lambda:pytest.fail('effect replayed'))
    assert module.run(None,'global_install',lambda:42)==42
    assert ledger.report()['counts']=={'start':1,'result':1}


def test_validation_dispatch_records_actual_evidence(client,scratch):
    from harness_local.validation_service import dispatch
    from test_validation import plan,request
    ledger=ActivityLedger(selected(client)); ledger.initialize()
    p=plan(); r=request(p)
    source=scratch/'broken.py'; source.write_text('def broken(:')
    result,code=dispatch('static',dict(schema_version=1,plan=p.model_dump(),request=r.model_dump(),
        source_path=str(source),activity_context=context(client)))
    assert code==1 and result['evidence']['status']=='failed'
    assert ledger.report()['failed_operations']==1


def test_publication_adapter_records_blocked_gate_without_remote_effect(client):
    from harness_local.publication import PublicationService
    from test_publication import Remote,make_intent,authorization
    from test_story_contracts import binding
    ledger=ActivityLedger(selected(client)); ledger.initialize()
    remote=Remote()
    service=PublicationService(binding(),remote,ledger.state,candidate_check=lambda i:'candidate_stale',
        evaluation_check=lambda e:None,activity_context=context(client))
    intent=make_intent()
    result=service.publish(intent,authorization(intent),None)
    assert result['reason']=='candidate_stale'
    assert not remote.writes
    assert ledger.report()['blocked_operations']==1


def test_distribution_adapter_records_selected_client_only(client):
    from test_distribution import make_plan
    from harness_local.distribution import apply
    out=client['binding'].parent/'update-plan.json'
    make_plan(client,out=out)
    ledger=ActivityLedger(selected(client)); ledger.initialize()
    result,code=apply(client['target'],client['policy'],out,activity_context=context(client))
    assert code==0
    assert (client['target']/'managed.md').read_bytes()==b'new\n'
    assert ledger.report()['counts']=={'start':1,'result':1}
    from harness_local.distribution import recover
    recover(client['target'],client['policy'],out,apply_changes=True)
    assert (client['target']/'managed.md').read_bytes()==b'old\n'
    assert ledger.report()['counts']=={'start':2,'result':2}


def test_publication_reconciles_final_ledger_failure_without_duplicate_effect(client,monkeypatch):
    from harness_local.publication import PublicationService
    from test_publication import Remote,make_intent,authorization
    from test_story_contracts import binding
    ledger=ActivityLedger(selected(client)); ledger.initialize()
    remote=Remote()
    service=PublicationService(binding(),remote,ledger.state,candidate_check=lambda i:None,
        evaluation_check=lambda e:None,activity_context=context(client))
    original=ActivityLedger.ingest
    def fail(self,events=(),usage=()):
        if any(e.get('kind')=='result' for e in events): raise ConfigError('ledger_unavailable')
        return original(self,events,usage)
    intent=make_intent(); approval=authorization(intent)
    monkeypatch.setattr(ActivityLedger,'ingest',fail)
    with pytest.raises(ConfigError): service.publish(intent,approval,None)
    assert remote.writes==['push','create_pr']
    monkeypatch.setattr(ActivityLedger,'ingest',original)
    assert service.publish(intent,approval,None)['status']=='published'
    assert remote.writes==['push','create_pr']
    assert ledger.report()['incomplete_operations']==0
    before=ledger.report()['counts']
    assert service.publish(intent,approval,None)['status']=='published'
    assert ledger.report()['counts']==before


def test_validation_rejects_foreign_plan_before_execution_or_ledger_write(client,scratch):
    from harness_local.validation_service import dispatch
    from test_validation import plan,request
    ledger=ActivityLedger(selected(client)); ledger.initialize()
    p=plan(client_id='beta'); r=request(p)
    with pytest.raises(ConfigError,match='ledger_identity_mismatch'):
        dispatch('static',dict(schema_version=1,plan=p.model_dump(),request=r.model_dump(),
            source_path=str(scratch/'absent.py'),activity_context=context(client)))
    assert ledger.report()['counts']=={}


def test_story_binding_is_recorded_once(hu):
    from harness_local.publication import bind_story
    from harness_core.story import StoryPlanBinding
    from test_publication import make_intent
    from test_hu_lifecycle import approved
    service,client,_=hu
    state=approved(service)['run']
    ledger=ActivityLedger(selected(client)); ledger.initialize()
    value=StoryPlanBinding(schema_version=1,client_id='alpha',checkout_id='checkout',hu_id='HU1',attempt=1,
        plan_sha256=state['plan']['plan_sha256'],story=make_intent().story,confirmed=True,actor='operator')
    bind_story(service,value); bind_story(service,value)
    assert ledger.report()['counts']=={'start':1,'result':1}


from test_hu_lifecycle import hu


def test_remote_validation_reconciles_own_journal_after_ledger_result_loss(client,scratch,monkeypatch):
    from harness_local.validation_service import dispatch
    import harness_local.validation_remote as remote_module
    from test_validation_remote import ServiceDouble,target
    from test_validation import plan,request
    from harness_core.onboarding_plan import sha
    ledger=ActivityLedger(selected(client)); ledger.initialize()
    p=plan('sql',impacts=['delta']); t=target()
    r=request(p,'delta-semantic',runtime=t.runtime,runtime_sha256=sha(t.runtime.encode()),
        tool_sha256=t.notebook_sha256,command=['databricks','jobs','run-now','7','--profile',t.profile])
    service=ServiceDouble(); service.request=r
    real=remote_module.RemoteValidator
    monkeypatch.setattr(remote_module,'RemoteValidator',lambda path:real(path,service))
    raw=dict(schema_version=1,plan=p.model_dump(),request=r.model_dump(),target=t.model_dump(),
        state_dir=str(scratch),mode='delta',expected={'rows':3,'sum':'30.00'},activity_context=context(client))
    original=ActivityLedger.ingest
    def fail(self,events=(),usage=()):
        if any(e.get('kind')=='result' for e in events): raise ConfigError('ledger_unavailable')
        return original(self,events,usage)
    monkeypatch.setattr(ActivityLedger,'ingest',fail)
    with pytest.raises(ConfigError): dispatch('remote',raw)
    monkeypatch.setattr(ActivityLedger,'ingest',original)
    assert dispatch('remote',raw)[0]['evidence']['status']=='passed'
    assert service.calls.count('submit')==1
    assert ledger.report()['incomplete_operations']==0


def test_reconciler_rejects_changed_request_before_effect(client):
    ledger=ActivityLedger(selected(client)); ledger.initialize()
    module=api()
    module.run(context(client),'publication',lambda:{'status':'published'},reconciler=True,request_sha256='a'*64)
    with pytest.raises(ConfigError,match='ledger_operation_conflict'):
        module.run(context(client),'publication',lambda:pytest.fail('changed request executed'),reconciler=True,request_sha256='b'*64)


def test_distribution_rollback_resolves_original_apply_pending(client,monkeypatch):
    from test_distribution import make_plan
    from harness_local.distribution import apply,recover
    out=client['binding'].parent/'update-plan.json'; make_plan(client,out=out)
    ledger=ActivityLedger(selected(client)); ledger.initialize()
    original=ActivityLedger.ingest
    def fail(self,events=(),usage=()):
        if any(e.get('kind')=='result' for e in events): raise ConfigError('ledger_unavailable')
        return original(self,events,usage)
    monkeypatch.setattr(ActivityLedger,'ingest',fail)
    with pytest.raises(ConfigError): apply(client['target'],client['policy'],out,activity_context=context(client))
    monkeypatch.setattr(ActivityLedger,'ingest',original)
    assert recover(client['target'],client['policy'],out,apply_changes=True)[1]==0
    assert (client['target']/'managed.md').read_bytes()==b'old\n'
    assert ledger.report()['incomplete_operations']==0


def test_invalid_activity_context_cli_does_not_leak_input(client,scratch,capsys):
    import json
    from harness_local.cli import main
    from test_validation import plan,request
    p=plan(); r=request(p)
    source=scratch/'input.json'
    source.write_text(json.dumps(dict(schema_version=1,plan=p.model_dump(),request=r.model_dump(),
        source_path=str(scratch/'source.py'),activity_context={'schema_version':99,'unexpected':'private-input'})))
    assert main(['validate','static','--input',str(source),'--json'])==2
    assert 'private-input' not in capsys.readouterr().out
