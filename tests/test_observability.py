import json

import pytest
from pydantic import ValidationError


def event(**changes):
    value = dict(schema_version=1, client_id='alpha', hu_id='HU1', attempt=1,
                 role='tester', event_id='test1', kind='test', source='harness-local',
                 observed_at='2026-10-13T10:00:00-05:00', duration_ms=12.0,
                 status='passed', payload={})
    value.update(changes)
    return value


def api():
    from harness_core import observability
    return observability


def test_duplicate_event_counted_once_with_provenance():
    q = api()
    records = [q.ActivityEvent.model_validate(event())] * 2
    result = q.activity_report(records, client_id='alpha', hu_id='HU1', attempt=1)
    assert result['counts'] == {'test': 1}
    assert result['duration_ms'] == 12
    assert result['duplicates'] == 1
    assert result['events'][0]['source'] == 'harness-local'
    assert result['coverage'] == 'submitted_events_only'


def test_duplicate_key_conflict_and_cross_client_fail_closed():
    q = api()
    from harness_core.configuration import ConfigError
    records = [q.ActivityEvent.model_validate(event()), q.ActivityEvent.model_validate(event(status='failed'))]
    with pytest.raises(ConfigError, match='event_id_conflict'):
        q.activity_report(records, client_id='alpha', hu_id='HU1', attempt=1)
    with pytest.raises(ConfigError, match='activity_identity_mismatch'):
        q.activity_report([records[0]], client_id='beta', hu_id='HU1', attempt=1)


def test_sensitive_payload_omitted_and_free_text_redacted():
    q = api()
    value = event(payload={'password': 'private-value', 'Authorization': 'Bearer private',
                           'nested': {'message': 'token=private-value'},
                           'note': 'ghp_' + 'a' * 30})
    record = q.ActivityEvent.model_validate(value)
    output = json.dumps(record.model_dump())
    assert 'private-value' not in output and 'Bearer private' not in output
    assert 'ghp_' not in output
    assert record.redacted


@pytest.mark.parametrize('change', [dict(schema_version=True), dict(schema_version=2),
    dict(observed_at='2026-99-40T00:00:00Z'), dict(observed_at='2026-10-13T00:00:00'),
    dict(attempt=0), dict(duration_ms=float('nan')), dict(extra=True)])
def test_strict_event_contract(change):
    with pytest.raises(ValidationError):
        api().ActivityEvent.model_validate(event(**change))


def test_desktop_usage_is_null_and_account_quota_never_distributed():
    q = api()
    usage = q.desktop_usage(client_id='alpha', hu_id='HU1', attempt=1,
                            observed_at='2026-10-13T10:00:00Z')
    assert usage.scope == 'hu' and usage.source == 'unavailable'
    assert usage.reason == 'supported_attributable_source_unavailable'
    assert all(getattr(usage, f) is None for f in ('input_tokens', 'output_tokens', 'cached_tokens', 'cost_usd'))
    with pytest.raises(ValidationError):
        q.UsageObservation.model_validate(dict(usage.model_dump(), input_tokens=100))


def test_supported_session_receipt_requires_association_and_units():
    q = api()
    value = dict(schema_version=1, client_id='alpha', hu_id='HU1', attempt=1,
                 source='supported-session-receipt', scope='session', surface='cli',
                 observed_at='2026-10-13T10:00:00Z', native_session_id='session1',
                 documentation_ref='https://example.org/usage-contract', association_ref='receipt1',
                 input_tokens=10, output_tokens=3, cached_tokens=2, cost_usd=None,
                 reason='billing_not_exposed')
    assert q.UsageObservation.model_validate(value).input_tokens == 10
    for change in (dict(association_ref=None), dict(native_session_id=None),
                   dict(scope='account'), dict(surface='desktop'), dict(cost_usd=1.0, reason=None)):
        with pytest.raises(ValidationError):
            q.UsageObservation.model_validate(dict(value, **change))


def test_usage_report_retains_activity_when_usage_unavailable():
    from harness_local.observability_service import usage_report
    result = usage_report(dict(schema_version=1, client_id='alpha', hu_id='HU1', attempt=1,
                               observed_at='2026-10-13T10:00:00Z', events=[event()]))
    assert result['status'] == 'partial'
    assert result['activity']['counts'] == {'test': 1}
    assert result['usage']['cost_usd'] is None


def test_credential_shaped_payload_key_is_never_exported():
    credential = 'ghp_' + 'a' * 30
    record = api().ActivityEvent.model_validate(event(payload={credential: 1, 'rows': 3}))
    assert credential not in json.dumps(record.model_dump())
    assert record.redacted and record.payload == {'rows': 3}
