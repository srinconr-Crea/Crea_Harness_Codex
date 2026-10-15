import importlib
import json
import sqlite3

import pytest

from harness_core.configuration import ConfigError
from harness_core.contracts import Binding


def api():
    assert importlib.util.find_spec('harness_local.activity_ledger'), 'activity ledger is missing'
    return importlib.import_module('harness_local.activity_ledger')


def selected(client):
    return Binding.model_validate(json.loads(client['binding'].read_bytes()))


def test_read_missing_does_not_create_state(client):
    ledger = api().ActivityLedger(selected(client))
    with pytest.raises(ConfigError, match='ledger_missing'):
        ledger.report()
    assert not ledger.state.exists()


def test_reopen_dedup_redaction_and_isolation(client):
    module = api()
    binding = selected(client)
    ledger = module.ActivityLedger(binding)
    ledger.initialize()
    event = dict(schema_version=1, client_id='alpha', checkout_id='checkout',
        event_id='e1', operation_id='op1', idempotency_key='start1', source='harness_commands',
        scope='setup', kind='start', observed_at='2026-10-14T10:00:00Z',
        payload={'stdout': 'private text', 'secret': 'hidden', 'count': 1})
    ledger.ingest([event])
    before = ledger.path.read_bytes()
    assert module.ActivityLedger(binding).report()['counts'] == {'start': 1}
    assert ledger.path.read_bytes() == before
    ledger.ingest([event])
    report = ledger.report()
    assert report['counts'] == {'start': 1}
    assert report['incomplete_operations'] == 1
    assert 'private text' not in json.dumps(report)
    assert 'hidden' not in json.dumps(report)
    foreign = binding.model_copy(update={'client_id': 'beta'})
    with pytest.raises(ConfigError, match='ledger_identity_mismatch'):
        module.ActivityLedger(foreign).report()
    with pytest.raises(ConfigError, match='ledger_identity_mismatch'):
        ledger.ingest([{**event, 'client_id': 'beta'}])


def test_unsupported_schema_never_reinitialized(client):
    ledger = api().ActivityLedger(selected(client))
    ledger.initialize()
    with sqlite3.connect(ledger.path) as db:
        db.execute('PRAGMA user_version=999')
    before = ledger.path.read_bytes()
    with pytest.raises(ConfigError, match='ledger_schema_unsupported'):
        ledger.initialize()
    assert ledger.path.read_bytes() == before


def test_operation_records_failure_and_blocks_when_busy(client):
    ledger = api().ActivityLedger(selected(client))
    ledger.initialize()
    with pytest.raises(ValueError, match='effect_failed'):
        with ledger.operation('op1', scope='hu', hu_id='HU1'):
            raise ValueError('effect_failed')
    report = ledger.report()
    assert report['failed_operations'] == 1
    assert report['incomplete_operations'] == 0
    assert report['duration_ms'] >= 0
    with sqlite3.connect(ledger.path) as db:
        db.execute('BEGIN IMMEDIATE')
        with pytest.raises(ConfigError, match='ledger_busy'):
            with ledger.operation('op2', scope='setup'):
                pytest.fail('effect ran without start record')
    assert ledger.report()['counts'] == {'start': 1, 'result': 1}


def test_export_exclusive_and_hu_database_untouched(client, scratch):
    ledger = api().ActivityLedger(selected(client))
    ledger.initialize()
    hu = ledger.state / 'hu.sqlite3'
    hu.write_bytes(b'existing lifecycle authority')
    out = scratch / 'report.json'
    ledger.export(out)
    with pytest.raises(ConfigError, match='destination_exists'):
        ledger.export(out)
    assert hu.read_bytes() == b'existing lifecycle authority'


def test_setup_creates_ledger_before_first_hu_and_preview_is_read_only(client, scratch):
    from harness_local import environment_setup as setup
    from test_environment_setup import supplied, snapshot
    from test_guided_onboarding import ready
    data = supplied(client)
    before = snapshot(scratch)
    result, code = setup.preview(data, probe_fn=ready)
    assert code == 0 and snapshot(scratch) == before
    parent = scratch / 'parent.json'
    parent.write_text(json.dumps(result['plan']))
    setup.apply(parent, result['plan']['plan_sha256'], probe_fn=ready)
    ledger = api().ActivityLedger(selected(client))
    assert ledger.report()['counts']['start'] >= 1
    assert all(e['hu_id'] is None for e in ledger.report()['events'])
    count = ledger.report()['counts']
    setup.apply(parent, result['plan']['plan_sha256'], probe_fn=ready)
    assert ledger.report()['counts'] == count


def test_activity_cli_missing_init_report_import_and_export(client, scratch, capsys):
    from harness_local.cli import main
    common = ['--path',str(client['target']),'--policy',str(client['policy']),'--binding',str(client['binding']),'--json']
    assert main(['activity','status',*common]) != 0
    assert json.loads(capsys.readouterr().out)['reason'] == 'ledger_missing'
    assert main(['activity','init',*common]) == 0
    capsys.readouterr()
    assert main(['activity','report',*common]) == 0
    assert json.loads(capsys.readouterr().out)['report']['input_tokens'] is None
    assert main(['activity','export',*common,'--out',str(scratch/'export.json')]) == 0
    capsys.readouterr()
    assert (scratch/'export.json').exists()


def test_hu_records_real_blocked_result_and_replay_not_counted(hu):
    service, client, _ = hu
    from test_hu_lifecycle import plan
    ledger = api().ActivityLedger(selected(client)); ledger.initialize()
    assert plan(service)['status'] == 'ready'
    assert plan(service)['idempotent']
    result = service.run('transition','HU1','bad-transition',dict(schema_version=1,state='implementing'))
    assert result['status'] == 'blocked'
    report = ledger.report()
    assert report['counts'] == {'start': 2, 'result': 2}
    assert [e['status'] for e in report['events'] if e['kind']=='result'] == ['passed','blocked']


from test_hu_lifecycle import hu


def test_migration_is_explicit_and_backed_up(client, scratch):
    ledger=api().ActivityLedger(selected(client)); ledger.initialize()
    with sqlite3.connect(ledger.path) as db:
        db.execute('PRAGMA user_version=1')
    with pytest.raises(ConfigError,match='ledger_schema_unsupported'):
        ledger.report()
    backup=scratch/'activity-v1.sqlite3'
    ledger.migrate(backup)
    assert ledger.report()['counts']=={}
    with sqlite3.connect(backup) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0]==1


def test_foreign_result_cannot_reassociate_operation(client):
    ledger=api().ActivityLedger(selected(client)); ledger.initialize()
    base=dict(schema_version=1,client_id='alpha',checkout_id='checkout',source='imported',scope='hu',
        hu_id='HU1',operation_id='op1',observed_at='2026-10-14T00:00:00Z')
    ledger.ingest([{**base,'event_id':'e1','idempotency_key':'k1','kind':'start'}])
    with pytest.raises(ConfigError,match='activity_association_mismatch'):
        ledger.ingest([{**base,'hu_id':'HU2','event_id':'e2','idempotency_key':'k2','kind':'result','status':'passed'}])


def test_usage_attribution_overlap_and_invalid_billing(client):
    ledger=api().ActivityLedger(selected(client)); ledger.initialize()
    usage=dict(schema_version=1,client_id='alpha',checkout_id='checkout',hu_id='HU1',attempt=1,
        source_event_id='receipt1',source='supported-session-receipt',surface='cli',scope='session',
        observed_at='2026-10-14T00:00:00Z',period_start='2026-10-14T00:00:00Z',period_end='2026-10-14T00:01:00Z',
        native_session_id='session1',documentation_ref='https://example.invalid/receipt',association_ref='binding1',
        input_tokens=10,output_tokens=5,cached_tokens=0,cost_usd=None,reason='billing_adapter_unavailable')
    ledger.ingest(usage=[usage,usage])
    assert len(ledger.report()['usage'])==1
    ledger.ingest(usage=[{**usage,'source_event_id':'receipt2'}])
    assert ledger.report()['measurement_conflicts']==['overlapping_usage_scopes']
    with pytest.raises(ConfigError,match='event_invalid'):
        ledger.ingest(usage=[{**usage,'source_event_id':'billing','surface':'desktop','cost_usd':2.0}])
    with pytest.raises(ConfigError,match='event_invalid'):
        ledger.ingest(usage=[{**usage,'source_event_id':'quota','scope':'account'}])


def test_setup_final_persist_failure_reconciles_without_repeating_stage(client,scratch,monkeypatch):
    from harness_local import environment_setup as setup
    from test_environment_setup import supplied
    from test_guided_onboarding import ready
    parent=scratch/'parent.json'
    result,_=setup.preview(supplied(client),probe_fn=ready,plan_out=parent)
    module=api(); original=module.ActivityLedger.ingest
    def fail(self,events=(),usage=()):
        if any(e.get('kind')=='result' for e in events): raise ConfigError('ledger_unavailable')
        return original(self,events,usage)
    monkeypatch.setattr(module.ActivityLedger,'ingest',fail)
    with pytest.raises(ConfigError): setup.apply(parent,result['plan']['plan_sha256'],probe_fn=ready)
    monkeypatch.setattr(module.ActivityLedger,'ingest',original)
    setup.recover(parent,result['plan']['plan_sha256'],probe_fn=ready)
    report=module.ActivityLedger(selected(client)).report()
    assert report['counts']=={'start':8,'result':8}
    assert report['incomplete_operations']==0


def test_existing_setup_journal_import_is_once_and_never_creates_hu(client,scratch):
    ledger=api().ActivityLedger(selected(client)); ledger.initialize()
    journal=dict(schema_version=1,plan_sha256='a'*64,stages=[{'name':'prepare','status':'completed'}, {'name':'check','status':'failed'}])
    ledger.import_setup_journal('setup-old',journal)
    before=ledger.report()
    ledger.import_setup_journal('setup-old',journal)
    assert ledger.report()==before
    assert before['counts']=={'start':2,'result':2}
    assert before['failed_operations']==1
    assert all(e['hu_id'] is None for e in before['events'])


def test_interrupt_leaves_pending_and_blocks_new_replay(client):
    ledger=api().ActivityLedger(selected(client)); ledger.initialize()
    with pytest.raises(KeyboardInterrupt):
        with ledger.operation('interrupted',scope='setup'): raise KeyboardInterrupt()
    assert ledger.report()['incomplete_operations']==1
    with pytest.raises(ConfigError,match='ledger_recovery_required'):
        with ledger.operation('interrupted',scope='setup'): pytest.fail('blind replay')


def test_setup_recovery_after_result_saved_before_pending_cleanup(client,scratch,monkeypatch):
    from harness_local import environment_setup as setup
    from test_environment_setup import supplied
    from test_guided_onboarding import ready
    parent=scratch/'parent.json'
    result,_=setup.preview(supplied(client),probe_fn=ready,plan_out=parent)
    original=setup.persist
    def interrupt(path,value):
        if isinstance(value,setup.SetupJournal) and any(s['status']=='completed' for s in value.stages) and not value.activity_operations:
            raise KeyboardInterrupt()
        return original(path,value)
    monkeypatch.setattr(setup,'persist',interrupt)
    with pytest.raises(KeyboardInterrupt): setup.apply(parent,result['plan']['plan_sha256'],probe_fn=ready)
    monkeypatch.setattr(setup,'persist',original)
    setup.recover(parent,result['plan']['plan_sha256'],probe_fn=ready)
    assert api().ActivityLedger(selected(client)).report()['counts']=={'start':8,'result':8}


def test_unavailable_usage_is_not_an_overlapping_measurement(client):
    ledger=api().ActivityLedger(selected(client)); ledger.initialize()
    usage=dict(schema_version=1,client_id='alpha',checkout_id='checkout',hu_id='HU1',attempt=1,
        source_event_id='none1',source='unavailable',scope='hu',reason='supported_attributable_source_unavailable',
        observed_at='2026-10-14T00:00:00Z',period_start='2026-10-14T00:00:00Z',period_end='2026-10-14T00:01:00Z')
    ledger.ingest(usage=[usage,{**usage,'hu_id':'HU2','source_event_id':'none2'}])
    assert ledger.report()['measurement_conflicts']==[]


def test_invalid_query_returns_structured_cli_error(client,capsys):
    from harness_local.cli import main
    ledger=api().ActivityLedger(selected(client)); ledger.initialize()
    common=['activity','report','--path',str(client['target']),'--policy',str(client['policy']),
        '--binding',str(client['binding']),'--json']
    assert main([*common,'--attempt','0'])==2
    assert json.loads(capsys.readouterr().out)['reason']=='invalid_ledger_query'


def test_retry_opening_is_attributed_to_new_attempt(hu):
    service,client,_=hu
    ledger=api().ActivityLedger(selected(client)); ledger.initialize()
    service.run('transition','HU1','failed',dict(schema_version=1,state='failed'))
    assert service.run('attempt','HU1','retry',dict(schema_version=1))['run']['attempt']==2
    events=ledger.report(dict(schema_version=1,hu_id='HU1',attempt=2))['events']
    assert [e['action'] for e in events]==['attempt','attempt']


def test_human_activity_report_shows_metrics_and_unavailable_usage(client,capsys):
    from harness_local.cli import main
    ledger=api().ActivityLedger(selected(client)); ledger.initialize()
    assert main(['activity','report','--path',str(client['target']),'--policy',str(client['policy']),
        '--binding',str(client['binding'])])==0
    output=capsys.readouterr().out
    assert 'Operaciones pendientes: 0' in output
    assert 'supported_attributable_source_unavailable' in output


def test_unavailable_disk_blocks_before_adapter_effect(client,monkeypatch):
    ledger=api().ActivityLedger(selected(client)); ledger.initialize()
    def unavailable(*args,**kwargs): raise sqlite3.OperationalError('disk unavailable')
    monkeypatch.setattr(sqlite3,'connect',unavailable)
    with pytest.raises(ConfigError,match='ledger_unavailable'):
        with ledger.operation('blocked',scope='setup'): pytest.fail('effect executed')


def test_two_client_ledgers_remain_separate(client,scratch):
    binding=selected(client)
    first=api().ActivityLedger(binding); first.initialize()
    second=api().ActivityLedger(binding.model_copy(update={'client_id':'beta','state_dir':str(scratch/'state/beta/checkout')}))
    second.initialize()
    with first.operation('alpha-operation',scope='setup'): pass
    assert first.report()['counts']=={'start':1,'result':1}
    assert second.report()['counts']=={}


def test_reused_hu_detects_setup_before_mutation_and_requires_ledger(hu):
    from test_setup_hu_scope import attach
    from test_hu_lifecycle import plan
    service,client,_=hu
    attach(service,client,initialize_activity=False)
    ledger=api().ActivityLedger(selected(client))
    assert not ledger.path.exists()
    before=(service.state/'hu.sqlite3').read_bytes()
    with pytest.raises(ConfigError,match='ledger_missing'):
        plan(service,paths=['src/total.py'])
    assert (service.state/'hu.sqlite3').read_bytes()==before
