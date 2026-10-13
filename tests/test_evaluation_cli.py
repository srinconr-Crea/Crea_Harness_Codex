import json

import pytest

from harness_local.cli import main
from test_agent_evaluation import bundle, profile
from test_observability import event


def call(scratch, capsys, command, action, value):
    path = scratch / 'input.json'
    path.write_text(json.dumps(value), encoding='utf-8')
    code = main([command, action, '--input', str(path), '--json'])
    return code, json.loads(capsys.readouterr().out)


def test_eval_cli_validate_and_incomplete_manual_batch(scratch, capsys):
    value = dict(schema_version=1, milestone=6, purpose='promotion',
                 profiles=[profile().model_dump()], runs=[], budget_runs=63, execution_mode='manual')
    code, result = call(scratch, capsys, 'eval', 'validate', value)
    assert code == 0 and result['status'] == 'valid' and not result['promotion_allowed']
    for action in ('run', 'report'):
        code, result = call(scratch, capsys, 'eval', action, value)
        assert code == 1 and result['status'] == 'blocked'
        assert result['required_runs'] == 63
        assert len(result['profiles'][0]['matrix']) == 63


def test_cli_usage_redacts_credentials_and_retains_counters(scratch, capsys):
    value = dict(schema_version=1, client_id='alpha', hu_id='HU1', attempt=1,
                 observed_at='2026-10-13T10:00:00Z',
                 events=[event(payload={'password': 'hidden', 'message': 'Bearer hidden'})])
    code, result = call(scratch, capsys, 'usage', 'report', value)
    assert code == 0 and result['status'] == 'partial'
    assert 'hidden' not in json.dumps(result)
    assert result['activity']['counts'] == {'test': 1}


@pytest.mark.parametrize('value', [dict(schema_version=99, password='hidden'),
    dict(schema_version=True), dict(schema_version=1, milestone=7), dict(unrecognized='hidden')])
def test_invalid_eval_inputs_never_echo_payload(scratch, capsys, value):
    code, result = call(scratch, capsys, 'eval', 'run', value)
    assert code == 2 and result['status'] == 'invalid' and 'hidden' not in json.dumps(result)


def test_duplicate_keys_and_nonfinite_input_rejected(scratch, capsys):
    path = scratch / 'input.json'
    for content in ('{"schema_version":1,"schema_version":1}', '{"duration_ms":NaN}'):
        path.write_text(content)
        assert main(['usage', 'report', '--input', str(path), '--json']) == 2
        assert json.loads(capsys.readouterr().out)['status'] == 'invalid'


def test_json_schemas_match_contracts_and_examples():
    from importlib.resources import files
    from harness_core.observability import ActivityEvent, UsageObservation, desktop_usage
    from harness_core.evaluation import EvalProfile, EvalRun, EvalScore
    from harness_local.evaluation_service import EvalInput
    from harness_local.observability_service import UsageInput
    import jsonschema
    models = (ActivityEvent, UsageObservation, EvalProfile, EvalRun, EvalScore, EvalInput, UsageInput)
    for model in models:
        schema = json.loads(files('harness_core').joinpath(f'schemas/{model.__name__.lower()}.schema.json').read_bytes())
        assert schema == model.model_json_schema()
        jsonschema.Draft202012Validator.check_schema(schema)
    example = desktop_usage(client_id='alpha', hu_id='HU1', attempt=1, observed_at='2026-10-13T00:00:00Z')
    jsonschema.validate(example.model_dump(), UsageObservation.model_json_schema())
    jsonschema.validate(profile().model_dump(), EvalProfile.model_json_schema())
