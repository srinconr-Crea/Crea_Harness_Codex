import hashlib
import json
from pathlib import Path

import pytest

from harness_core.configuration import ConfigError
from harness_core.desktop import activate_profiles
from harness_core.guided import QuestionnaireDraft, GuidedOnboardingPlan, CertificationInput
from harness_core.onboarding_plan import canonical, sha
from harness_local import guided_onboarding as guided
from harness_local.desktop_resources import load_desktop
from harness_local.onboarding import preview as init_preview
from harness_local.diagnostics import Check


def ready(name): return Check(name, 'ready', 'compatible', 'synthetic')


def snapshot(root):
    return {str(p.relative_to(root)): sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}


def setup(client, *, custom=False, proposed=False):
    data = json.loads(client['policy'].read_text())
    data['read_only_paths'] = []
    client['policy'].write_text(json.dumps(data))
    binding = json.loads(client['binding'].read_text())
    binding['policy_sha256'] = sha(client['policy'].read_bytes())
    client['binding'].write_text(json.dumps(binding))
    if custom: (client['target'] / 'AGENTS.md').write_text('# Instrucciones propias\nConservar negocio.\n')
    catalog = activate_profiles(load_desktop(), {'auditor': {'model': 'test-model', 'effort': 'medium'}}, {'test-model': ['medium']})
    values = dict(target_path=str(client['target']), policy_path=str(client['policy']), binding_path=str(client['binding']),
        catalog=catalog.model_dump(), development=dict(schema_version=1, client_id='alpha', stack=['Python'],
            conventions=['pytest'], business_rules=['Regla sintética alpha'], roles=['auditor'], validations=['pytest'],
            sources={'stack': 'user', 'conventions': 'user', 'business_rules': 'user', 'roles': 'user', 'validations': 'user'}),
        tool_binding=dict(schema_version=1, client_id='alpha', checkout_id='checkout', tools=[]))
    if proposed:
        client['binding'].unlink()
        values.update(binding_mode='proposed', state_dir=binding['state_dir'], repository='demo/alpha', base_branch='develop')
        (client['target'] / '.harness/client.yaml').unlink()
    draft = QuestionnaireDraft(schema_version=1, answers={k: dict(value=v, status='known', source='user', confirmed=True) for k,v in values.items()})
    path = client['policy'].parent / 'guided-plan.json'
    return draft, path, catalog


def test_preview_snapshot_exclusive_export_and_custom_agents(client):
    draft, path, _ = setup(client, custom=True)
    before = snapshot(client['target'].parent)
    result, code = guided.preview(draft, probe_fn=ready)
    assert code == 0 and result['plan']['init_v1']['applicable'] is False
    assert result['plan']['preparation']['kind'] == 'composite_preparation_plan'
    assert not any(o['path'] == 'AGENTS.md' for o in result['plan']['preparation']['operations'])
    assert snapshot(client['target'].parent) == before
    guided.preview(draft, probe_fn=ready, plan_out=path)
    exported = snapshot(client['target'].parent)
    with pytest.raises(ConfigError): guided.preview(draft, probe_fn=ready, plan_out=path)
    assert snapshot(client['target'].parent) == exported
    v1, _ = init_preview(client['target'], client['policy'], client['binding'], probe_fn=ready)
    assert not v1['applicable']


@pytest.mark.parametrize('custom,proposed', [(False, False), (True, True)])
def test_explicit_stages_repeat_recovery_and_context_separation(client, custom, proposed):
    draft, path, _ = setup(client, custom=custom, proposed=proposed)
    original = snapshot(client['target'])
    guided.preview(draft, probe_fn=ready, plan_out=path)
    with pytest.raises(ConfigError): guided.apply(path, stage='integrate', probe_fn=ready)
    prepared, code = guided.apply(path, stage='prepare', probe_fn=ready)
    assert code == 0 and prepared['prepared'] and not prepared['certified']
    assert prepared['remote_not_checked'] and prepared['status'] == 'partial'
    assert not (client['target'] / '.codex/config.toml').exists()
    assert (client['target'] / '.harness/development.yaml').exists()
    assert 'Regla sintética alpha' in (client['target'] / '.harness/context.md').read_text(encoding='utf-8')
    assert 'Regla sintética alpha' not in Path('src/harness_local/guided_kit/harness-client-onboarding/SKILL.md').read_text(encoding='utf-8')
    before = snapshot(client['target'].parent)
    repeated, _ = guided.apply(path, stage='prepare', probe_fn=ready)
    assert repeated['idempotent'] and snapshot(client['target'].parent) == before
    integrated, _ = guided.apply(path, stage='integrate', probe_fn=ready)
    assert integrated['prepared'] and integrated['stages']['integrate'] == 'completed'
    if custom: assert (client['target'] / 'AGENTS.md').read_text().startswith('# Instrucciones propias')
    after = snapshot(client['target'].parent)
    assert guided.apply(path, stage='integrate', probe_fn=ready)[0]['idempotent']
    assert snapshot(client['target'].parent) == after
    recovery, _ = guided.recover(path, stage='integrate')
    assert recovery['recovery_status'] == 'preview' and snapshot(client['target'].parent) == after
    guided.recover(path, stage='integrate', apply_changes=True)
    recovered, code=guided.recover(path, stage='prepare', apply_changes=True)
    assert code==0 and recovered['recovery_status']=='recovered'
    assert snapshot(client['target']) == original
    assert not (client['target']/'.agents').exists()
    assert client['binding'].exists() is not proposed


def test_protected_bootstrap_cross_client_and_missing_tools(client):
    draft, path, _ = setup(client)
    policy = json.loads(client['policy'].read_text())
    policy['read_only_paths'] = ['.harness/']
    client['policy'].write_text(json.dumps(policy))
    binding = json.loads(client['binding'].read_text()); binding['policy_sha256'] = sha(client['policy'].read_bytes())
    client['binding'].write_text(json.dumps(binding))
    before = snapshot(client['target'].parent)
    blocked, code = guided.preview(draft, probe_fn=ready)
    assert code == 1 and 'policy_denied' in blocked['plan']['blockers']
    assert snapshot(client['target'].parent) == before
    other = draft.model_dump(); other['answers']['tool_binding']['value']['client_id'] = 'beta'
    with pytest.raises(ConfigError): guided.preview(QuestionnaireDraft.model_validate(other), probe_fn=ready)
    assert snapshot(client['target'].parent) == before
    missing = lambda name: Check(name, 'missing', 'not_found', 'synthetic missing tool')
    blocked, code = guided.preview(draft, probe_fn=missing)
    assert code == 1 and not blocked['plan']['preparation']['applicable']


def test_interview_unknown_target_and_discovery_no_inferred_permission(client):
    result, code = guided.preview(QuestionnaireDraft(schema_version=1, answers={}), probe_fn=ready)
    assert code == 1 and result['questions']
    draft, _, _ = setup(client)
    values = draft.model_dump(); values['answers']['target_path']['confirmed'] = False
    result, code = guided.preview(QuestionnaireDraft.model_validate(values), probe_fn=ready)
    assert code == 1 and result['questions'][0]['field'] == 'target_path'


@pytest.mark.parametrize('fault', ['before_binding', 'after_binding', 'integration'])
def test_stage_fault_journal_no_fake_rollback_and_recovery(client, monkeypatch, fault):
    draft, path, _ = setup(client, proposed=True)
    original = snapshot(client['target'])
    guided.preview(draft, probe_fn=ready, plan_out=path)
    def fail(point):
        if point == fault: raise ConfigError('synthetic_fault')
    monkeypatch.setattr(guided, 'checkpoint', fail)
    stage = 'prepare'
    if fault == 'integration':
        guided.apply(path, stage='prepare', probe_fn=ready)
        stage = 'integrate'
    result, code = guided.apply(path, stage=stage, probe_fn=ready)
    assert code == 1 and result['stages'][stage] == 'failed'
    assert result['recovery_required']
    if fault == 'integration': assert result['prepared']
    with pytest.raises(ConfigError): guided.apply(path, stage=stage, probe_fn=ready)
    if fault == 'integration': guided.recover(path, stage='integrate', apply_changes=True)
    guided.recover(path, stage='prepare', apply_changes=True)
    assert snapshot(client['target']) == original and not client['binding'].exists()


def test_stale_plan_and_modified_owned_file_conflict(client):
    draft, path, _ = setup(client, custom=True)
    guided.preview(draft, probe_fn=ready, plan_out=path)
    (client['target'] / 'AGENTS.md').write_text('Changed before apply')
    before = snapshot(client['target'].parent)
    with pytest.raises(ConfigError): guided.apply(path, stage='prepare', probe_fn=ready)
    assert snapshot(client['target'].parent) == before
    path.unlink()
    guided.preview(draft, probe_fn=ready, plan_out=path)
    guided.apply(path, stage='prepare', probe_fn=ready)
    (client['target'] / '.harness/context.md').write_text('Manual change')
    result, code = guided.recover(path, stage='prepare', apply_changes=True)
    assert code == 1 and result['recovery_status'] == 'conflict'
    assert (client['target'] / '.harness/context.md').read_text() == 'Manual change'


def test_accepted_limitation_separate_from_certification_and_required_block(client):
    from harness_core.desktop import DesktopCertificate, DesktopObservation
    from harness_core.supervised import SupervisedAcceptance
    from harness_local.supervised import capture
    draft, path, catalog = setup(client)
    guided.preview(draft, probe_fn=ready, plan_out=path)
    guided.apply(path, stage='prepare', probe_fn=ready)
    guided.apply(path, stage='integrate', probe_fn=ready)
    (client['target'] / 'src').mkdir(); (client['target'] / 'src/example.py').write_text('x = 1')
    certificate = DesktopCertificate(schema_version=1, catalog_sha256=catalog.sha256,
        app_version='synthetic', engine_version='not_exposed', account_ref='synthetic', observations=[
        DesktopObservation(schema_version=1, role='auditor', surface=s, status='observed', evidence_ref='synthetic',
            model='test-model' if s == 'model-effort' else None, effort='medium' if s == 'model-effort' else None,
            effective_sandbox='workspace-write' if s == 'permissions' else None)
        for s in ('role', 'model-effort', 'permissions', 'skill:harness-hu', 'tool:local-files', 'tool:git')])
    captured = capture(client['target'], client['policy'], client['binding'], ['src'], catalog.sha256, certificate)
    acceptance = SupervisedAcceptance(schema_version=1, client_id='alpha', checkout_id='checkout',
        catalog_sha256=catalog.sha256, candidate_sha256=captured.sha256, evidence_sha256=captured.evidence_sha256,
        operator_ref='human', accepted=True, limitations=['auditor:permissions', 'auditor:tool:databricks'])
    evidence = CertificationInput(schema_version=1, certificate=certificate, snapshot=captured,
        acceptance=acceptance, required_capabilities=[])
    result, code = guided.apply(path, stage='certify', evidence=evidence, probe_fn=ready)
    assert code == 0 and result['supervised_preparation_accepted'] and not result['certified']
    assert 'auditor:permissions' in result['limitations']
    repeated, _ = guided.apply(path,stage='prepare',probe_fn=ready)
    assert repeated['supervised_preparation_accepted'] and repeated['limitations'] == result['limitations']
    blocked, code = guided.apply(path, stage='certify', evidence=evidence.model_copy(update={'required_capabilities':['auditor:permissions']}), probe_fn=ready)
    assert code == 1 and blocked['prepared'] and not blocked['supervised_preparation_accepted']
    assert blocked['blocked_required'] == ['auditor:permissions'] and not blocked['certified']


def test_linked_export_and_preserved_identity_replacement(client, scratch):
    import os
    draft,path,_=setup(client,custom=True)
    original=scratch/'original.json'; original.write_text('keep')
    os.link(original,path)
    with pytest.raises(ConfigError): guided.preview(draft,probe_fn=ready,plan_out=path)
    assert original.read_text() == 'keep'
    path.unlink(); guided.preview(draft,probe_fn=ready,plan_out=path)
    guided.apply(path,stage='prepare',probe_fn=ready)
    agents=client['target']/'AGENTS.md'; content=agents.read_bytes(); agents.unlink(); agents.write_bytes(content)
    with pytest.raises(ConfigError): guided.apply(path,stage='integrate',probe_fn=ready)


def test_discovery_and_ambiguous_candidates_need_confirmation(client):
    draft,_,_=setup(client)
    facts=guided.discover(draft)
    assert any(f['field']=='repository' and f['value']=='demo/alpha' for f in facts)
    assert all(f['source']=='local' and f['confirmed'] is False for f in facts)
    values=draft.model_dump(); values['answers']['target_path']['value']=[str(client['target']), 'C:/other']
    result,code=guided.preview(QuestionnaireDraft.model_validate(values),probe_fn=ready)
    assert code==1 and result['questions'][0]['reason']=='ambiguous_target'


def test_integration_recovery_conflict_returns_report(client):
    draft,path,_=setup(client)
    guided.preview(draft,probe_fn=ready,plan_out=path)
    guided.apply(path,stage='prepare',probe_fn=ready); guided.apply(path,stage='integrate',probe_fn=ready)
    owned=client['target']/'.codex/agents/harness-auditor.toml'; owned.write_text('Manual personalization')
    result,code=guided.recover(path,stage='integrate',apply_changes=True)
    assert code==1 and result['recovery_status']=='conflict' and result['conflicts']
    assert owned.read_text()=='Manual personalization'


def test_certification_candidate_drift_blocks_even_strict_desktop(client):
    from harness_core.desktop import DesktopCertificate, DesktopObservation, assess_certificate
    from harness_core.supervised import SupervisedAcceptance
    from harness_local.supervised import capture
    draft,path,catalog=setup(client)
    guided.preview(draft,probe_fn=ready,plan_out=path)
    guided.apply(path,stage='prepare',probe_fn=ready); guided.apply(path,stage='integrate',probe_fn=ready)
    candidate=client['target']/'candidate.txt'; candidate.write_text('before')
    observations=[DesktopObservation(schema_version=1,role='auditor',surface=s,status='observed',evidence_ref='synthetic',
        model='test-model' if s=='model-effort' else None,effort='medium' if s=='model-effort' else None,
        effective_sandbox='read-only' if s=='permissions' else None)
        for s in ('role','model-effort','permissions','skill:harness-hu','tool:local-files','tool:git','tool:databricks')]
    certificate=DesktopCertificate(schema_version=1,catalog_sha256=catalog.sha256,app_version='synthetic',engine_version='synthetic',account_ref='synthetic',observations=observations)
    assert assess_certificate(catalog,certificate)['certified']
    captured=capture(client['target'],client['policy'],client['binding'],['candidate.txt'],catalog.sha256,certificate)
    acceptance=SupervisedAcceptance(schema_version=1,client_id='alpha',checkout_id='checkout',catalog_sha256=catalog.sha256,
        candidate_sha256=captured.sha256,evidence_sha256=captured.evidence_sha256,operator_ref='human',accepted=True,limitations=[])
    evidence=CertificationInput(schema_version=1,certificate=certificate,snapshot=captured,acceptance=acceptance,required_capabilities=[])
    candidate.write_text('changed')
    result,code=guided.apply(path,stage='certify',evidence=evidence,probe_fn=ready)
    assert code==1 and not result['certified'] and result['strict_certificate']['certified']
    assert not result['candidate_comparison']['intact'] and result['candidate_comparison']['differences']


def test_two_clients_no_leak(client, scratch):
    draft, path, _ = setup(client)
    guided.preview(draft, probe_fn=ready, plan_out=path)
    guided.apply(path, stage='prepare', probe_fn=ready)
    before = snapshot(client['target'])
    import subprocess
    beta = scratch / 'beta'; beta.mkdir()
    subprocess.run(['git','init','--initial-branch=develop',str(beta)],check=True,capture_output=True)
    subprocess.run(['git','-C',str(beta),'remote','add','origin','https://github.com/demo/beta.git'],check=True,capture_output=True)
    policy = json.loads(client['policy'].read_text()); policy.update(client_id='beta', repository='demo/beta')
    bp = scratch/'beta-policy.json'; bp.write_text(json.dumps(policy))
    values = draft.model_dump()
    for key,val in dict(target_path=str(beta),policy_path=str(bp),binding_path=str(scratch/'beta-binding.json'),binding_mode='proposed',
        state_dir=str(scratch/'state/beta/other'),repository='demo/beta',base_branch='develop').items():
        values['answers'][key] = dict(value=val,status='known',source='user',confirmed=True)
    values['answers']['development']['value'].update(client_id='beta',business_rules=['Only beta'])
    values['answers']['tool_binding']['value'].update(client_id='beta',checkout_id='other')
    bplan = scratch/'beta-plan.json'
    guided.preview(QuestionnaireDraft.model_validate(values),probe_fn=ready,plan_out=bplan)
    guided.apply(bplan,stage='prepare',probe_fn=ready)
    assert snapshot(client['target']) == before
    assert 'alpha' not in (beta/'.harness/context.md').read_text(encoding='utf-8')
