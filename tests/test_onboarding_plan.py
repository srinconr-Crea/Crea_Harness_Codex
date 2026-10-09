import hashlib
import json

import pytest

from harness_core.configuration import ConfigError
from harness_local.onboarding import preview


def inputs(client):
    data = json.loads(client['policy'].read_text())
    data['read_only_paths'] = []
    client['policy'].write_text(json.dumps(data))
    return dict(binding_out=client['binding'].parent / 'new-binding.json', checkout_id='new',
                state_dir=client['binding'].parent / 'state/alpha/new')


def test_binding_proposal_export_determinism(client):
    kw = inputs(client)
    destination = client['binding'].parent / 'plan.json'
    a, _ = preview(client['target'], client['policy'], None, **kw)
    b, _ = preview(client['target'], client['policy'], None, **kw, plan_out=destination)
    assert a['plan'] == b['plan']
    assert a['applicable'] is True
    assert not kw['binding_out'].exists() and not kw['state_dir'].exists()
    assert len(a['plan']['operations']) == 10  # AGENTS + eight OpenSpec + binding
    assert destination.exists()
    with pytest.raises(ConfigError, match='export_exists'):
        preview(client['target'], client['policy'], None, **kw, plan_out=destination)
    from harness_core.onboarding_plan import load_plan
    assert load_plan(destination).plan_sha256 == a['plan']['plan_sha256']
    data = json.loads(destination.read_text())
    data['operations'][0]['content'] = 'arbitrary'
    destination.write_text(json.dumps(data))
    with pytest.raises(ConfigError, match='invalid_plan'):
        load_plan(destination)


@pytest.mark.parametrize('path', ['a/../b', 'CON', 'a:ads', 'a.', 'a ', '.harness/aux.txt', 'a\\b'])
def test_windows_destination_aliases(path):
    from harness_core.onboarding_plan import destination_path
    with pytest.raises(ConfigError):
        destination_path(path)


def test_policy_applies_to_bootstrap(client):
    kw = inputs(client)
    (client['target'] / '.harness/client.yaml').unlink()
    data = json.loads(client['policy'].read_text())
    data['read_only_paths'] = ['.harness/']
    client['policy'].write_text(json.dumps(data))
    result, code = preview(client['target'], client['policy'], None, repo='demo/alpha', base_branch='develop', **kw)
    assert code == 1 and result['applicable'] is False
    assert any(c['code'] == 'policy_denied' for c in result['checks'])


def test_strict_plan_duplicate_secret_version_and_size(client):
    from harness_core.onboarding_plan import load_plan
    result, _ = preview(client['target'], client['policy'], None, **inputs(client))
    path = client['binding'].parent / 'bad-plan.json'
    for data in [dict(result['plan'], schema_version=2), dict(result['plan'], api_token='x')]:
        path.write_text(json.dumps(data))
        with pytest.raises(ConfigError):
            load_plan(path)
    path.write_text('{"schema_version":1,"schema_version":1}')
    with pytest.raises(ConfigError, match='duplicate_key'):
        load_plan(path)
    path.write_bytes(b' ' * (1024 * 1024 + 1))
    with pytest.raises(ConfigError, match='document_too_large'):
        load_plan(path)


@pytest.mark.parametrize('field,value', [('max_files', 1), ('max_bytes', 1), ('denied_paths', ['.agents/**'])])
def test_policy_limits(client, field, value):
    kw = inputs(client)
    data = json.loads(client['policy'].read_text())
    data[field] = value
    client['policy'].write_text(json.dumps(data))
    report, code = preview(client['target'], client['policy'], None, **kw)
    assert report['applicable'] is False and code == 1


def test_export_overlap_and_missing_binding_fields(client):
    kw = inputs(client)
    for path in (client['target'] / 'plan.json', kw['state_dir'] / 'plan.json', client['policy']):
        with pytest.raises(ConfigError):
            preview(client['target'], client['policy'], None, **kw, plan_out=path)
    with pytest.raises(ConfigError):
        preview(client['target'], client['policy'], None, binding_out=kw['binding_out'])
