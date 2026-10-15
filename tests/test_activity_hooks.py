import importlib
import json

import pytest

from harness_core.configuration import ConfigError
from harness_local.activity_ledger import ActivityLedger
from test_activity_ledger import selected


def api():
    assert importlib.util.find_spec('harness_local.activity_hooks'), 'hook adapter missing'
    return importlib.import_module('harness_local.activity_hooks')


def test_hook_missing_or_untrusted_keeps_own_ledger_operational(client):
    ledger=ActivityLedger(selected(client)); ledger.initialize()
    result=api().diagnose(events=[],trusted=False,script=None)
    assert result['reason']=='native_actions_not_observed'
    with ledger.operation('own',scope='setup'): pass
    assert ledger.report()['counts']=={'start':1,'result':1}


def test_hook_explicit_session_association_dedup_and_foreign_rejection(client):
    ledger=ActivityLedger(selected(client)); ledger.initialize()
    association=dict(schema_version=1,client_id='alpha',checkout_id='checkout',session_id='session1',
        target_path=str(client['target']),hu_id='HU1',attempt=1,confirmed=True)
    event=dict(hook_event_name='PostToolUse',session_id='session1',cwd=str(client['target']),
        tool_use_id='call1',tool_name='Bash',tool_input={'command':'secret conversation'},tool_response={'stdout':'private'})
    module=api()
    module.ingest(ledger,event,association,trusted=True,supported_events=['PostToolUse'])
    module.ingest(ledger,event,association,trusted=True,supported_events=['PostToolUse'])
    report=ledger.report()
    assert report['counts']=={'annotation':1}
    assert report['events'][0]['source']=='hooks'
    assert 'private' not in json.dumps(report) and 'secret conversation' not in json.dumps(report)
    with pytest.raises(ConfigError,match='usage_unattributable'):
        module.ingest(ledger,{**event,'session_id':'other'},association,trusted=True,supported_events=['PostToolUse'])
    with pytest.raises(ConfigError,match='native_source_unavailable'):
        module.ingest(ledger,event,association,trusted=False,supported_events=['PostToolUse'])


def test_cli_hook_diagnosis_does_not_create_missing_ledger(client,capsys):
    from harness_local.cli import main
    assert main(['activity','diagnose-hooks','--path',str(client['target']),'--policy',str(client['policy']),
        '--binding',str(client['binding']),'--json'])==0
    result=json.loads(capsys.readouterr().out)
    assert result['hooks']['reason']=='native_actions_not_observed'
    assert not ActivityLedger(selected(client)).path.exists()


def test_hook_overlap_does_not_double_count_own_operation(client):
    ledger=ActivityLedger(selected(client)); ledger.initialize()
    with ledger.operation('own',scope='hu',hu_id='HU1',attempt=1): pass
    association=dict(schema_version=1,client_id='alpha',checkout_id='checkout',session_id='session1',
        target_path=str(client['target']),hu_id='HU1',attempt=1,confirmed=True,tool_operations={'call1':'own'})
    event=dict(hook_event_name='PostToolUse',session_id='session1',cwd=str(client['target']),tool_use_id='call1',tool_name='Bash')
    api().ingest(ledger,event,association,trusted=True,supported_events=['PostToolUse'])
    assert ledger.report()['counts']=={'start':1,'result':1}


@pytest.mark.parametrize('events,trusted,script',[([],True,__file__),(['PostToolUse'],False,__file__),(['PostToolUse'],True,None)])
def test_incompatible_untrusted_or_missing_script_is_partial_only(events,trusted,script):
    result=api().diagnose(events=events,trusted=trusted,script=script)
    assert result['reason']=='native_actions_not_observed' and result['tokens'] is None
