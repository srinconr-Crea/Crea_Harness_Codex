import json
from pathlib import Path

import pytest

from harness_core.configuration import ConfigError
from harness_core.desktop import DesktopCertificate, DesktopObservation, activate_profiles, assess_certificate
from harness_local.desktop_resources import load_desktop
from harness_core.supervised import SupervisedAcceptance, assess_preparation
from harness_local.supervised import capture, compare, prepare


def context(client):
    catalog = activate_profiles(load_desktop(), {'auditor': {'model': 'test-model', 'effort': 'medium'}}, {'test-model': ['medium']})
    certificate = DesktopCertificate(schema_version=1, catalog_sha256=catalog.sha256,
        app_version='test-app', engine_version='not_exposed', account_ref='synthetic', observations=[
        DesktopObservation(schema_version=1, role='auditor', surface=s, status='observed', evidence_ref='probe',
            model='test-model' if s == 'model-effort' else None, effort='medium' if s == 'model-effort' else None,
            effective_sandbox='workspace-write' if s == 'permissions' else None)
        for s in ('role', 'model-effort', 'permissions', 'skill:harness-hu', 'tool:local-files', 'tool:git')])
    (client['target'] / 'src').mkdir()
    (client['target'] / 'src/a.py').write_text('original')
    snapshot = capture(client['target'], client['policy'], client['binding'], ['src', 'new.py'], catalog.sha256, certificate)
    acceptance = SupervisedAcceptance(schema_version=1, client_id='alpha', checkout_id='checkout',
        catalog_sha256=catalog.sha256, candidate_sha256=snapshot.sha256, evidence_sha256=snapshot.evidence_sha256,
        operator_ref='human', accepted=True, limitations=['auditor:permissions', 'auditor:tool:databricks'])
    return catalog, certificate, snapshot, acceptance


def test_intact_supervised_review_keeps_strict_conflict(client):
    catalog, certificate, snapshot, acceptance = context(client)
    result = assess_preparation(catalog, certificate, snapshot, acceptance)
    assert result['prepared'] and not result['certified']
    assert result['strict_certificate']['status'] == 'blocked'
    assert compare(client['target'], client['policy'], client['binding'], snapshot, certificate)['status'] == 'ready'
    assert not assess_certificate(catalog, certificate)['certified']


@pytest.mark.parametrize('mutation', ['change', 'add', 'delete', 'absent'])
def test_candidate_drift_blocks_without_reverting(client, mutation):
    _, certificate, snapshot, _ = context(client)
    path = client['target'] / ('new.py' if mutation == 'absent' else 'src/a.py')
    if mutation == 'delete': path.unlink()
    elif mutation == 'add': (client['target'] / 'src/new.py').write_text('added')
    else: path.write_text('changed')
    result = compare(client['target'], client['policy'], client['binding'], snapshot, certificate)
    assert result['status'] == 'blocked' and result['differences']
    if mutation != 'delete': assert path.exists()


@pytest.mark.parametrize('field', ['client_id', 'checkout_id', 'catalog_sha256', 'candidate_sha256', 'evidence_sha256', 'accepted', 'limitations'])
def test_stale_or_missing_acceptance_blocks(client, field):
    catalog, certificate, snapshot, acceptance = context(client)
    assert not assess_preparation(catalog, certificate, snapshot, None)['prepared']
    value = acceptance.model_dump()
    value[field] = False if field == 'accepted' else ([] if field == 'limitations' else ('b' * 64 if field.endswith('sha256') else 'other'))
    altered = SupervisedAcceptance.model_validate(value)
    assert not assess_preparation(catalog, certificate, snapshot, altered)['prepared']


def test_failed_capability_blocks_phase_despite_acceptance(client):
    catalog, certificate, snapshot, acceptance = context(client)
    assert not assess_preparation(catalog, certificate, snapshot, acceptance, required=['auditor:permissions'])['prepared']
    assert not assess_preparation(catalog, certificate, snapshot, acceptance, required=['auditor:unknown'])['prepared']


def test_evidence_or_selected_identity_drift_rejected(client):
    _, certificate, snapshot, _ = context(client)
    other = certificate.model_copy(update={'app_version': 'other'})
    with pytest.raises(ConfigError): compare(client['target'], client['policy'], client['binding'], snapshot, other)
    value = json.loads(client['binding'].read_text())
    value['checkout_id'] = 'other'
    value['state_dir'] = str(Path(value['state_dir']).parent / 'other')
    client['binding'].write_text(json.dumps(value))
    with pytest.raises(ConfigError): compare(client['target'], client['policy'], client['binding'], snapshot, certificate)


def test_windows_target_case_alias_preserves_identity(client):
    _, certificate, snapshot, _ = context(client)
    alias = client['target'].parent / client['target'].name.upper()
    assert compare(alias, client['policy'], client['binding'], snapshot, certificate)['intact']


@pytest.mark.parametrize('scope', ['private', '.git', 'evidence', '../outside', 'src/a.py/child'])
def test_snapshot_rejects_denied_or_unsafe_scopes(client, scope):
    catalog, certificate, _, _ = context(client)
    with pytest.raises(ConfigError): capture(client['target'], client['policy'], client['binding'], [scope], catalog.sha256, certificate)


def test_preparation_requires_intact_applied_integration(client, scratch):
    from harness_local.desktop_integration import preview, apply
    catalog, certificate, snapshot, acceptance = context(client)
    plan = scratch / 'integration.json'
    preview(client['target'], client['policy'], client['binding'], catalog, plan_out=plan)
    with pytest.raises((ConfigError, OSError)):
        prepare(client['target'], client['policy'], client['binding'], plan, catalog, certificate, snapshot, acceptance)
    apply(client['target'], client['policy'], plan)
    result = prepare(client['target'], client['policy'], client['binding'], plan, catalog, certificate, snapshot, acceptance)
    assert result['prepared'] and not result['certified']
    (client['target'] / '.codex/agents/harness-auditor.toml').write_text('changed')
    with pytest.raises(ConfigError):
        prepare(client['target'], client['policy'], client['binding'], plan, catalog, certificate, snapshot, acceptance)


def test_core_rejects_non_desktop_discovery(client):
    catalog, certificate, snapshot, acceptance = context(client)
    for o in certificate.observations: o.source = 'files'
    snapshot = capture(client['target'], client['policy'], client['binding'], ['src'], catalog.sha256, certificate)
    acceptance = acceptance.model_copy(update={'candidate_sha256': snapshot.sha256, 'evidence_sha256': snapshot.evidence_sha256,
        'limitations': [f'auditor:{s}' for s in ('role', 'model-effort', 'permissions', 'skill:harness-hu', 'tool:local-files', 'tool:git', 'tool:databricks')]})
    assert not assess_preparation(catalog, certificate, snapshot, acceptance)['prepared']


def test_reject_hardlink_and_size_limit(client):
    import os
    catalog, certificate, _, _ = context(client)
    os.link(client['target'] / 'src/a.py', client['target'] / 'src/link.py')
    with pytest.raises(ConfigError): capture(client['target'], client['policy'], client['binding'], ['src'], catalog.sha256, certificate)
    (client['target'] / 'src/link.py').unlink()
    (client['target'] / 'src/a.py').write_bytes(b'x' * (2 * 1024 * 1024 + 1))
    with pytest.raises(ConfigError): capture(client['target'], client['policy'], client['binding'], ['src'], catalog.sha256, certificate)


def test_cli_snapshot_export_and_compare(client, scratch, capsys):
    from harness_local.cli import main
    catalog, certificate, _, _ = context(client)
    catalog_file = scratch / 'catalog.json'
    observations = scratch / 'observations.json'
    catalog_file.write_text(json.dumps(catalog.model_dump()))
    observations.write_text(json.dumps(certificate.model_dump()))
    out = scratch / 'candidate.json'
    common = ['--path', str(client['target']), '--policy', str(client['policy']), '--binding', str(client['binding']),
        '--catalog', str(catalog_file), '--observations', str(observations), '--json']
    assert main(['review-snapshot', *common, '--scope', 'src', '--out', str(out)]) == 0
    assert json.loads(capsys.readouterr().out)['command'] == 'review-snapshot'
    assert main(['review-snapshot', *common, '--scope', 'src', '--out', str(out)]) == 1
    capsys.readouterr()
    assert main(['review-compare', *common, '--snapshot', str(out)]) == 0
    capsys.readouterr()
    (client['target'] / 'src/a.py').write_text('modified')
    assert main(['review-compare', *common, '--snapshot', str(out)]) == 1
    assert json.loads(capsys.readouterr().out)['differences']
