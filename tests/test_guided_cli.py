import json

import pytest

from harness_local.cli import main


def test_cli_interview_reports_missing_only(scratch, capsys):
    config = scratch/'interview.json'
    config.write_text(json.dumps(dict(schema_version=1,answers={})))
    assert main(['onboard','--config',str(config),'--dry-run','--json']) == 1
    result = json.loads(capsys.readouterr().out)
    assert result['command'] == 'onboard' and result['status'] == 'blocked'
    assert {q['field'] for q in result['questions']} == {'target_path','policy_path','binding_path','development','tool_binding','catalog'}


@pytest.mark.parametrize('args', [[], ['--apply'], ['--dry-run','--stage','prepare'],
    ['--apply','--plan','missing.json','--stage','unknown'], ['--recover-apply','--dry-run'],
    ['--apply','--config','missing.json','--stage','prepare'], ['--recover','--plan','missing.json','--stage','certify']])
def test_cli_invalid_stage_authorization_never_writes(args, capsys):
    assert main(['onboard',*args,'--json']) == 2
    result = json.loads(capsys.readouterr().out)
    assert result['command'] == 'onboard' and result['status'] == 'invalid'


def test_cli_secret_redacted(scratch,capsys):
    path=scratch/'secret.json'; secret='password=synthetic-sensitive'
    path.write_text(json.dumps(dict(schema_version=1,answers={'target_path':dict(value=secret,status='known',source='user',confirmed=True)})))
    assert main(['onboard','--config',str(path),'--dry-run','--json']) == 2
    output=capsys.readouterr().out
    assert secret not in output and 'secret_not_allowed' in output


def test_recovery_human_output_after_preview_and_apply(client,capsys):
    from test_guided_onboarding import setup,ready
    from harness_local import guided_onboarding as guided
    draft,path,_=setup(client)
    guided.preview(draft,probe_fn=ready,plan_out=path); guided.apply(path,stage='prepare',probe_fn=ready)
    for extra in ([],['--recover-apply']):
        assert main(['onboard','--recover','--plan',str(path),'--stage','prepare',*extra])==0
        output=capsys.readouterr().out
        assert 'onboard: partial' in output and 'recovery_status:' in output


def test_invalid_human_flags_return_code_without_traceback(capsys):
    assert main(['onboard'])==2
    assert 'onboard: invalid' in capsys.readouterr().out
