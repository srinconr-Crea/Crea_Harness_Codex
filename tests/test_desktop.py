import json
from pathlib import Path
import tomllib

import pytest
from pydantic import ValidationError

from harness_core.configuration import ConfigError
from harness_core.desktop import (
    RoleCatalog, RoleAssignment, DesktopCertificate, DesktopObservation,
    activate_profiles, check_assignments, assess_certificate,
)
from harness_local.desktop_resources import load_desktop, render_integration
from harness_local.desktop_integration import preview, apply, recover


def profiles():
    catalog = load_desktop()
    selected = {r.id: {'model': 'account-model', 'effort': 'high'} for r in catalog.roles}
    return activate_profiles(catalog, selected, {'account-model': ['high']})


def plan_for(client, **options):
    return preview(client['target'], client['policy'], client['binding'], profiles(), **options)


def exported(client, scratch):
    path = scratch / 'integration.json'
    result, code = plan_for(client, plan_out=path)
    assert code == 0
    return path, result


def test_catalog_and_templates_have_bounded_roles_and_passive_practices():
    catalog = load_desktop()
    assert {r.id for r in catalog.roles} == {
        'principal', 'analyst', 'impact-analyzer', 'planner', 'developer', 'tester', 'auditor', 'verifier'}
    assert all(not r.activated and r.model is None for r in catalog.roles)
    content = render_integration(profiles())
    assert '.agents/skills/harness-hu/SKILL.md' in content
    assert 'practices.json' in content['.agents/skills/harness-hu/SKILL.md']
    config = tomllib.loads(content['.codex/config.toml'])
    assert len(config['agents']) == 8
    for role in catalog.roles:
        agent = tomllib.loads(content[f'.codex/agents/harness-{role.id}.toml'])
        assert agent['model'] == 'account-model'
        assert agent['model_reasoning_effort'] == 'high'
        assert agent['sandbox_mode'] == role.sandbox
        assert role.inputs and role.outputs and role.tools


def test_no_silent_model_fallback_and_no_unselected_profiles():
    catalog = load_desktop()
    with pytest.raises(ConfigError, match='model_unavailable'):
        activate_profiles(catalog, {'developer': {'model': 'missing', 'effort': 'high'}}, {})
    with pytest.raises(ConfigError, match='effort_unavailable'):
        activate_profiles(catalog, {'developer': {'model': 'account-model', 'effort': 'max'}},
                          {'account-model': ['high']})
    with pytest.raises(ConfigError):
        activate_profiles(catalog, {'unknown': {'model': 'x', 'effort': 'high'}}, {'x': ['high']})


def test_assignment_single_writer_nested_case_alias_and_isolation():
    catalog = profiles()
    def assignment(role, paths, isolation='checkout-a'):
        return RoleAssignment(schema_version=1, role=role, write_paths=paths, isolation=isolation)
    assert check_assignments(catalog, [assignment('principal', [])]) is None
    with pytest.raises(ConfigError, match='writer_collision'):
        check_assignments(catalog, [assignment('developer', ['src/']), assignment('tester', ['SRC/a.py'])])
    check_assignments(catalog, [assignment('developer', ['src/']), assignment('tester', ['src/a.py'], 'checkout-b')])
    with pytest.raises(ConfigError, match='read_only_assignment'):
        check_assignments(catalog, [assignment('auditor', ['src/a.py'])])
    with pytest.raises(ConfigError, match='delegation_limit'):
        check_assignments(catalog, [assignment('developer', ['a']), assignment('tester', ['b']),
                                   assignment('planner', []), assignment('analyst', []), assignment('verifier', [])])


def test_strict_versions_fields_and_generated_schemas():
    from jsonschema import validate
    catalog = load_desktop()
    schema = json.loads(Path('schemas/rolecatalog.schema.json').read_text())
    validate(catalog.model_dump(), schema)
    with pytest.raises(ValidationError):
        RoleCatalog.model_validate({**catalog.model_dump(), 'schema_version': 2})
    with pytest.raises(ValidationError):
        RoleCatalog.model_validate({**catalog.model_dump(), 'surprise': True})


def test_preview_snapshot_and_exclusive_export(client, scratch):
    before = {str(p): p.read_bytes() for p in client['target'].rglob('*') if p.is_file()}
    result, code = plan_for(client)
    assert code == 0 and result['status'] == 'ready'
    assert before == {str(p): p.read_bytes() for p in client['target'].rglob('*') if p.is_file()}
    assert not Path(json.loads(client['binding'].read_text())['state_dir']).exists()
    assert result['desktop_status'] == 'not_checked'
    path, _ = exported(client, scratch)
    before_plan = path.read_bytes()
    with pytest.raises(ConfigError):
        plan_for(client, plan_out=path)
    assert path.read_bytes() == before_plan


def test_custom_agents_and_toml_preserved_and_recovered(client, scratch):
    target = client['target']
    original = b'# Cliente\r\nReglas personalizadas.\r\n'
    (target / 'AGENTS.md').write_bytes(original)
    (target / '.codex').mkdir()
    toml = b'# Preferencias\n[features]\ncustom = true\n'
    (target / '.codex/config.toml').write_bytes(toml)
    path, planned = exported(client, scratch)
    assert planned['plan']['edits'][0]['old_hash'] is not None
    result, code = apply(target, client['policy'], path)
    assert code == 0
    assert (target / 'AGENTS.md').read_bytes().startswith(original)
    assert (target / '.codex/config.toml').read_bytes().startswith(toml)
    assert result['desktop_status'] == 'not_checked'
    dry, code = recover(target, client['policy'], path)
    assert code == 0 and dry['status'] == 'ready'
    restored, code = recover(target, client['policy'], path, apply_changes=True)
    assert code == 0
    assert (target / 'AGENTS.md').read_bytes() == original
    assert (target / '.codex/config.toml').read_bytes() == toml
    assert not (target / '.agents/skills/harness-hu/SKILL.md').exists()


def test_drift_rejected_before_any_target_or_state_write(client, scratch):
    target = client['target']
    (target / 'AGENTS.md').write_text('original')
    path, _ = exported(client, scratch)
    (target / 'AGENTS.md').write_text('changed')
    with pytest.raises(ConfigError, match='integration_drift'):
        apply(target, client['policy'], path)
    assert (target / 'AGENTS.md').read_text() == 'changed'
    assert not (target / '.codex').exists()
    assert not Path(json.loads(client['binding'].read_text())['state_dir']).exists()


def test_recovery_modification_and_replacement_identity_conflict(client, scratch):
    path, _ = exported(client, scratch)
    apply(client['target'], client['policy'], path)
    file = client['target'] / '.codex/agents/harness-developer.toml'
    file.write_text('custom = true')
    result, code = recover(client['target'], client['policy'], path, apply_changes=True)
    assert code == 1 and result['status'] == 'blocked'
    assert file.read_text() == 'custom = true'
    assert (client['target'] / 'AGENTS.md').exists()  # preflight all before recovery


def test_policy_and_foreign_client_block(client, scratch):
    policy = json.loads(client['policy'].read_text())
    policy['denied_paths'].append('.codex/')
    client['policy'].write_text(json.dumps(policy))
    with pytest.raises(ConfigError):
        plan_for(client)


def test_foreign_checkout_cannot_apply_plan(client, scratch):
    path, _ = exported(client, scratch)
    other = scratch / 'foreign'
    other.mkdir()
    with pytest.raises(ConfigError, match='integration_identity_mismatch'):
        apply(other, client['policy'], path)


def test_existing_owned_config_conflict_has_no_automatic_merge(client):
    target = client['target']
    (target / '.codex').mkdir()
    (target / '.codex/config.toml').write_text('[agents.harness-developer]\nconfig_file="mine.toml"\n')
    with pytest.raises(ConfigError, match='integration_conflict'):
        plan_for(client)


def observation(surface, role='developer', status='observed', **kwargs):
    return DesktopObservation(schema_version=1, role=role, surface=surface, status=status,
        evidence_ref='synthetic-observation', **kwargs)


def certificate(catalog, observations):
    return DesktopCertificate(schema_version=1, catalog_sha256=catalog.sha256,
        app_version='test-app', engine_version='test-engine', account_ref='sanitized-account',
        observations=observations)


def test_files_cli_never_certify_and_missing_required_tool_blocks():
    catalog = profiles()
    assert assess_certificate(catalog, certificate(catalog, []))['desktop_status'] == 'not_checked'
    result = assess_certificate(catalog, certificate(catalog, [observation('role', source='cli')]))
    assert result['certified'] is False
    observations = [observation('tool:local-files', status='unavailable')]
    assert assess_certificate(catalog, certificate(catalog, observations))['status'] == 'blocked'


def test_effective_permission_and_hook_coverage_are_independent():
    catalog = profiles()
    observations = [observation('permissions', role='auditor', effective_sandbox='workspace-write')]
    result = assess_certificate(catalog, certificate(catalog, observations))
    assert result['certified'] is False and result['status'] == 'blocked'
    result = assess_certificate(catalog, certificate(catalog, [observation('hook:before-tool', status='unsupported')]))
    assert result['certified'] is False


def test_matching_desktop_observations_certify_only_requested_roles():
    catalog = activate_profiles(load_desktop(), {'developer': {'model': 'account-model', 'effort': 'high'}},
                               {'account-model': ['high']})
    role = next(r for r in catalog.roles if r.id == 'developer')
    observations = [observation('role'), observation('model-effort', model='account-model', effort='high'),
        observation('skill:harness-hu'), observation('permissions', effective_sandbox=role.sandbox)]
    observations += [observation('tool:' + t.id) for t in role.tools if t.required]
    result = assess_certificate(catalog, certificate(catalog, observations))
    assert result['certified'] is True
    observations[1] = observation('model-effort', model='other', effort='high')
    assert assess_certificate(catalog, certificate(catalog, observations))['status'] == 'blocked'


def test_export_hardlink_and_target_junction_rejected(client, scratch):
    import os
    import subprocess
    existing = scratch / 'existing'
    existing.write_text('preserve')
    link = scratch / 'linked'
    os.link(existing, link)
    with pytest.raises(ConfigError):
        plan_for(client, plan_out=link)
    outside = scratch / 'outside'
    outside.mkdir()
    subprocess.run(['cmd', '/c', 'mklink', '/J', str(client['target'] / '.codex'), str(outside)],
                   check=True, capture_output=True)
    with pytest.raises(ConfigError):
        plan_for(client)
    assert not list(outside.iterdir())


def test_hashed_equal_replacement_is_not_owned(client, scratch):
    path, _ = exported(client, scratch)
    apply(client['target'], client['policy'], path)
    file = client['target'] / 'AGENTS.md'
    raw = file.read_bytes()
    file.rename(file.with_suffix('.user'))
    file.write_bytes(raw)
    result, code = recover(client['target'], client['policy'], path, apply_changes=True)
    assert code == 1 and 'AGENTS.md' in result['conflicts']
    assert file.read_bytes() == raw


def test_invalid_backup_cannot_restore_any_file(client, scratch):
    (client['target'] / 'AGENTS.md').write_text('client rules')
    path, planned = exported(client, scratch)
    apply(client['target'], client['policy'], path)
    backup = Path(planned['plan']['binding']['state_dir']) / ('desktop-' + planned['plan']['run_id']) / '00.bak'
    backup.write_text('not the backup')
    before = (client['target'] / 'AGENTS.md').read_bytes()
    result, code = recover(client['target'], client['policy'], path, apply_changes=True)
    assert code == 1 and (client['target'] / 'AGENTS.md').read_bytes() == before


def test_resources_altered_fail_closed(monkeypatch, scratch):
    import shutil
    import harness_local.desktop_resources as module
    shutil.copytree('src/harness_local/desktop_kit', scratch / 'desktop_kit')
    (scratch / 'desktop_kit/agents/developer.md').write_text('wrong')
    monkeypatch.setattr(module, 'files', lambda _: scratch)
    with pytest.raises(ConfigError, match='desktop_resources_invalid'):
        load_desktop()


def test_cli_invalid_and_check_output_are_versioned(capsys, scratch):
    from harness_local.cli import main
    assert main(['integrate', '--dry-run', '--json']) == 2
    invalid = json.loads(capsys.readouterr().out)
    assert invalid['schema_version'] == 1 and invalid['command'] == 'integrate'
    catalog = profiles()
    catalog_path = scratch / 'catalog.json'
    catalog_path.write_text(catalog.model_dump_json(), encoding='utf-8')
    observation_path = scratch / 'observations.json'
    observation_path.write_text(certificate(catalog, []).model_dump_json(), encoding='utf-8')
    assert main(['desktop-check', '--catalog', str(catalog_path), '--observations', str(observation_path), '--json']) == 0
    report = json.loads(capsys.readouterr().out)
    assert report['status'] == 'partial' and report['certified'] is False


@pytest.mark.parametrize('persist_first', [True, False])
def test_interrupted_recovery_resumes_persisted_recovered_records(client, scratch, monkeypatch, persist_first):
    import harness_local.desktop_integration as module
    (client['target'] / 'AGENTS.md').write_text('original rules')
    path, _ = exported(client, scratch)
    apply(client['target'], client['policy'], path)
    persist = module.persist
    def interrupted(path, journal):
        if persist_first:
            persist(path, journal)
        if any(r.state == 'recovered' for r in journal.records):
            raise OSError('synthetic interruption')
    monkeypatch.setattr(module, 'persist', interrupted)
    with pytest.raises(OSError):
        recover(client['target'], client['policy'], path, apply_changes=True)
    monkeypatch.setattr(module, 'persist', persist)
    result, code = recover(client['target'], client['policy'], path, apply_changes=True)
    assert code == 0 and result['recovery_status'] == 'recovered'
    assert (client['target'] / 'AGENTS.md').read_text() == 'original rules'


def test_secret_original_never_exported_in_report(client):
    (client['target'] / 'AGENTS.md').write_text('sk-' + 'A' * 30)
    with pytest.raises(ConfigError, match='secret_not_allowed'):
        plan_for(client)


def test_toml_credential_field_never_exported(client):
    (client['target'] / '.codex').mkdir()
    (client['target'] / '.codex/config.toml').write_text('[mcp_servers.private.env]\nAPI_KEY = "synthetic-value"\n')
    with pytest.raises(ConfigError, match='secret_not_allowed'):
        plan_for(client)


def test_multibyte_payload_is_bounded_for_recovery(client):
    (client['target'] / 'AGENTS.md').write_bytes(('á' * 65500).encode('utf-8'))
    with pytest.raises(ConfigError, match='document_too_large'):
        plan_for(client)
