import copy
import json

import pytest
from pydantic import ValidationError

from harness_core.configuration import ConfigError
from harness_core.onboarding_plan import sha, canonical
from harness_core.distribution import InstallationBinding, ReleaseManifest, UpdatePlan, PilotReport
from harness_local.distribution import candidate_manifest, bootstrap, preview, apply, recover, release_gate


def setup(client):
    target = client['target']
    (target / 'managed.md').write_bytes(b'old\n')
    manifest = candidate_manifest()
    value = manifest.model_dump(exclude={'manifest_sha256'})
    value['resources']['managed.md'] = sha(b'new\n')
    manifest = ReleaseManifest.model_validate({**value, 'manifest_sha256': sha(canonical(value))})
    binding = InstallationBinding(schema_version=1, binding_path=str(client['binding']),
        release_sha256=manifest.manifest_sha256, files={'managed.md': sha(b'old\n')})
    upstream = {'managed.md': 'new\n'}
    return target, manifest, binding, upstream


def make_plan(client, *, out=None):
    target, manifest, binding, upstream = setup(client)
    return preview(target, client['policy'], client['binding'], binding, manifest, upstream, plan_out=out)[0]['plan']


def test_candidate_pinned_and_unaccepted():
    m = candidate_manifest()
    assert m.certified is False and m.release_allowed is False
    assert m.resources and m.dependencies and m.sources
    assert all(v.sha256 and v.version and v.license for v in m.dependencies)
    assert all(v.sha256 and v.commit and v.license for v in m.sources)
    assert m.pending_acceptance
    ReleaseManifest.model_validate(m.model_dump())


@pytest.mark.parametrize('field', ['certified', 'release_allowed'])
def test_candidate_cannot_claim_certification(field):
    value = candidate_manifest().model_dump()
    value[field] = True
    with pytest.raises(ValidationError): ReleaseManifest.model_validate(value)


def test_bootstrap_has_no_side_effects(scratch):
    before = list(scratch.iterdir())
    result, code = bootstrap(detect=lambda _: None)
    assert code == 0 and result['status'] == 'partial'
    assert result['login'] == 'pending' and result['trust'] == 'pending'
    assert result['plugin'] == 'unsupported' and result['certified'] is False
    assert all(s['review_required'] for s in result['steps'])
    assert list(scratch.iterdir()) == before


def test_preview_no_writes_and_three_hashes(client):
    target, manifest, binding, upstream = setup(client)
    before = {str(p): p.read_bytes() for p in target.rglob('*') if p.is_file()}
    result, code = preview(target, client['policy'], client['binding'], binding, manifest, upstream)
    assert code == 0
    plan = UpdatePlan.model_validate(result['plan'])
    assert plan.edits[0].installed_hash == sha(b'old\n')
    assert plan.edits[0].local_hash == sha(b'old\n')
    assert plan.edits[0].upstream_hash == sha(b'new\n')
    assert not (client['binding'].parent / 'state').exists()
    assert before == {str(p): p.read_bytes() for p in target.rglob('*') if p.is_file()}


def test_personalization_conflict(client):
    target, manifest, binding, upstream = setup(client)
    (target / 'managed.md').write_bytes(b'personal\n')
    result, code = preview(target, client['policy'], client['binding'], binding, manifest, upstream)
    assert code == 1 and result['plan']['applicable'] is False
    assert result['conflicts'] == ['managed.md']
    assert (target / 'managed.md').read_bytes() == b'personal\n'


def test_update_and_recovery_preserve_state(client):
    out = client['binding'].parent / 'update-plan.json'
    plan = make_plan(client, out=out)
    result, code = apply(client['target'], client['policy'], out)
    assert code == 0 and result['status'] == 'ready'
    assert (client['target'] / 'managed.md').read_bytes() == b'new\n'
    state = json.loads(client['binding'].read_text())['state_dir']
    from pathlib import Path
    (Path(state) / 'user-state.txt').write_text('preserve')
    assert recover(client['target'], client['policy'], out)[0]['recovery_status'] == 'ready'
    assert recover(client['target'], client['policy'], out, apply_changes=True)[1] == 0
    assert (client['target'] / 'managed.md').read_bytes() == b'old\n'
    assert (Path(state) / 'user-state.txt').read_text() == 'preserve'
    assert recover(client['target'], client['policy'], out, apply_changes=True)[0]['recovery_status'] == 'already_recovered'
    assert plan['plan_sha256']


@pytest.mark.parametrize('operation', ['apply', 'recover'])
def test_drift_blocks_without_overwrite(client, operation):
    out = client['binding'].parent / 'update-plan.json'
    make_plan(client, out=out)
    if operation == 'recover': apply(client['target'], client['policy'], out)
    (client['target'] / 'managed.md').write_text('personal')
    if operation == 'apply':
        with pytest.raises(ConfigError): apply(client['target'], client['policy'], out)
    else:
        assert recover(client['target'], client['policy'], out, apply_changes=True)[1] == 1
    assert (client['target'] / 'managed.md').read_text() == 'personal'


def test_existing_export_preserved(client):
    out = client['binding'].parent / 'plan.json'
    out.write_text('personal')
    with pytest.raises(ConfigError): make_plan(client, out=out)
    assert out.read_text() == 'personal'


def test_export_inside_target_rejected(client):
    with pytest.raises(ConfigError): make_plan(client, out=client['target'] / 'plan.json')


@pytest.mark.parametrize('path', ['../escape', '.git/config', '.harness/client.yaml', 'kit.lock.json', 'C:/escape'])
def test_invalid_or_unowned_destinations(client, path):
    target, manifest, binding, upstream = setup(client)
    upstream[path] = 'x'
    with pytest.raises((ConfigError, ValidationError)):
        preview(target, client['policy'], client['binding'], binding, manifest, upstream)


def test_tampered_plan_rejected(client):
    out = client['binding'].parent / 'plan.json'
    value = make_plan(client, out=out)
    value['edits'][0]['content'] = 'tampered'
    out.write_bytes(canonical(value))
    with pytest.raises(ConfigError): apply(client['target'], client['policy'], out)


def test_other_checkout_rejected(client, scratch):
    out = client['binding'].parent / 'plan.json'
    make_plan(client, out=out)
    other = scratch / 'beta'
    other.mkdir()
    with pytest.raises(ConfigError): apply(other, client['policy'], out)


def test_repeat_apply_does_not_replace_backup(client):
    out = client['binding'].parent / 'plan.json'
    make_plan(client, out=out)
    apply(client['target'], client['policy'], out)
    with pytest.raises(ConfigError): apply(client['target'], client['policy'], out)
    assert recover(client['target'], client['policy'], out, apply_changes=True)[1] == 0


def test_release_pending_gate():
    report = PilotReport(schema_version=1, candidate_sha256=candidate_manifest().manifest_sha256,
        implementation_status='complete', receipts=[])
    result, code = release_gate(report)
    assert code == 1 and not result['certified'] and not result['release_allowed']
    assert not result['next_increment_enabled'] and not result['publication_allowed']
    assert result['pending']


@pytest.mark.parametrize('source', ['local_test', 'simulated', 'manual_git'])
def test_non_harness_receipts_never_certify(source):
    report = PilotReport(schema_version=1, candidate_sha256=candidate_manifest().manifest_sha256,
        implementation_status='complete', receipts=[dict(schema_version=1, protocol='harness_publication',
            status='passed', source=source, evidence_path='evidence.json', evidence_sha256='a'*64)])
    assert release_gate(report)[1] == 1


def test_contracts_reject_unknown_fields():
    with pytest.raises(ValidationError):
        InstallationBinding(schema_version=1, binding_path='x', release_sha256='a'*64, files={}, unknown=True)


def test_multibyte_content_cannot_exceed_recovery_limit(client):
    target, manifest, binding, upstream = setup(client)
    upstream['managed.md'] = 'á'*70000
    value=manifest.model_dump(exclude={'manifest_sha256'})
    value['resources']['managed.md']=sha(upstream['managed.md'].encode('utf-8'))
    manifest=ReleaseManifest.model_validate({**value,'manifest_sha256':sha(canonical(value))})
    with pytest.raises((ConfigError,ValidationError)):
        preview(target,client['policy'],client['binding'],binding,manifest,upstream)
    assert (target/'managed.md').read_bytes()==b'old\n'


def test_recover_checks_backup_integrity(client):
    from pathlib import Path
    out=client['binding'].parent/'plan.json'
    plan=make_plan(client,out=out)
    apply(client['target'],client['policy'],out)
    state=Path(json.loads(client['binding'].read_text())['state_dir'])
    (state/('update-'+plan['run_id'])/'00.bak').write_bytes(b'tampered')
    assert recover(client['target'],client['policy'],out,apply_changes=True)[1]==1
    assert (client['target']/'managed.md').read_bytes()==b'new\n'


def test_profile_cli_never_satisfies_desktop_gate(scratch,monkeypatch):
    import harness_local.evaluation_service as service
    def claimed_report(*_):
        return dict(required_runs=144,promotion_allowed=True,profiles=[]),0
    monkeypatch.setattr(service,'dispatch',claimed_report)
    batch=dict(milestone=7,purpose='promotion',profiles=[dict(surface='cli')])
    (scratch/'batch.json').write_bytes(canonical(batch))
    pilot=PilotReport(schema_version=1,candidate_sha256=candidate_manifest().manifest_sha256,
        implementation_status='complete',receipts=[],evaluation_path='batch.json',evaluation_sha256=sha(canonical(batch)))
    assert 'required_real_evals' in release_gate(pilot,evidence_root=scratch)[0]['pending']


def test_rehashed_plan_cannot_launder_personalized_lock(client):
    target,manifest,binding,upstream=setup(client)
    (target/'kit.lock.json').write_bytes(b'personal lock contents')
    out=client['binding'].parent/'plan.json'
    result,code=preview(target,client['policy'],client['binding'],binding,manifest,upstream,plan_out=out)
    assert code==1
    value=result['plan']
    edit=next(e for e in value['edits'] if e['path']=='kit.lock.json')
    edit['installed_hash']=edit['local_hash']
    edit['conflict']=False
    value['applicable']=True
    value['plan_sha256']=sha(canonical({k:v for k,v in value.items() if k!='plan_sha256'}))
    out.write_bytes(canonical(value))
    with pytest.raises(ConfigError): apply(target,client['policy'],out)
    assert (target/'kit.lock.json').read_bytes()==b'personal lock contents'


def test_T22_personalized_agent_toml_preserves_external_state(client):
    target,manifest,binding,_=setup(client)
    path='.codex/agents/harness-developer.toml'
    (target/'.codex/agents').mkdir(parents=True)
    original=b'model="installed"\n'
    personal=b'model="personal"\n'
    upstream='model="updated"\n'
    (target/path).write_bytes(personal)
    value=manifest.model_dump(exclude={'manifest_sha256'})
    value['resources'][path]=sha(upstream.encode())
    manifest=ReleaseManifest.model_validate({**value,'manifest_sha256':sha(canonical(value))})
    binding=binding.model_copy(update={'files':{path:sha(original)}})
    state=client['binding'].parent/'user-state.txt';state.write_text('preserve')
    result,code=preview(target,client['policy'],client['binding'],binding,manifest,{path:upstream})
    assert code==1 and result['conflicts']==[path]
    assert (target/path).read_bytes()==personal and state.read_text()=='preserve'


def test_failed_write_after_backup_can_recover(client,monkeypatch):
    from harness_local.windows_fs import Handle
    out=client['binding'].parent/'plan.json'
    make_plan(client,out=out)
    original=Handle.replace_bytes
    def fail_after_write(handle,data):
        original(handle,data)
        raise ConfigError('write_failed')
    monkeypatch.setattr(Handle,'replace_bytes',fail_after_write)
    assert apply(client['target'],client['policy'],out)[1]==1
    monkeypatch.setattr(Handle,'replace_bytes',original)
    assert recover(client['target'],client['policy'],out,apply_changes=True)[1]==0
    assert (client['target']/'managed.md').read_bytes()==b'old\n'
