"""Record measured local checks and complete scenario/protocol mapping."""
import json
from pathlib import Path
import re

from harness_local.distribution import candidate_manifest
from harness_core.onboarding_plan import sha

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/evidence'
TRACE={
    'Clean Windows machine':(['test_bootstrap_has_no_side_effects','test_launcher_clean_machine_preview_is_read_only'],['second_environment','new_user_desktop']),
    'Unsupported plugin capability':(['test_bootstrap_has_no_side_effects'],[]),
    'Unmodified managed file':(['test_update_and_recovery_preserve_state'],['update_recover']),
    'Locally modified file':(['test_personalization_conflict','test_rehashed_plan_cannot_launder_personalized_lock'],['update_recover']),
    'Accepted release':(['test_complete_import_gate_mechanics'],['second_environment','predecessor_evals','new_user_desktop']),
    'Modified post-update file':(['test_drift_blocks_without_overwrite'],['update_recover']),
    'Candidate with pending acceptance':(['test_release_pending_gate','test_complete_import_rejects_invalid_eval_identity'],['predecessor_evals']),
    'Preview snapshot':(['test_preview_no_writes_and_three_hashes'],[]),
    'Existing export destination':(['test_existing_export_preserved','test_export_inside_target_rejected'],[]),
    'Two clients':(['test_other_checkout_rejected'],['alpha_hu','beta_hu','client_isolation']),
    'Missing remote test':(['test_release_pending_gate','test_complete_import_rejects_bad_protocol'],['synthetic_client_pilot']),
    'Local development before predecessor acceptance':(['test_candidate_pinned_and_unaccepted','test_release_pending_gate'],['predecessor_evals','compatible_sandbox']),
    'Manual pilot does not certify harness publication':(['test_non_harness_receipts_never_certify','test_complete_import_rejects_bad_protocol'],['harness_publication']),
    'Synthetic client pilot':(['test_release_pending_gate'],['synthetic_client_pilot']),
    'Real data requested by fixture':(['test_release_pending_gate'],['synthetic_client_pilot']),
}


def main():
    manifest=candidate_manifest()
    change=ROOT/'openspec/changes/08-pilot-and-reproducible-distribution'
    tests='\n'.join(p.read_text(encoding='utf-8') for p in (ROOT/'tests').glob('test_distribution*.py'))
    protocols=json.loads((OUT/'distribution/protocols.json').read_bytes())
    ids={p['protocol'] for p in protocols['protocols']}
    scenarios=[]
    for delta in sorted((change/'specs').glob('*/spec.md')):
        main_spec=ROOT/'openspec/specs'/delta.parent.name/'spec.md'
        assert delta.read_text(encoding='utf-8').split('## ADDED Requirements',1)[1] == main_spec.read_text(encoding='utf-8').split('## Requirements',1)[1]
        for scenario in re.findall(r'^#### Scenario: (.+)$',delta.read_text(encoding='utf-8'),re.M):
            names,refs=TRACE[scenario]
            assert all('def '+n+'(' in tests for n in names)
            assert set(refs)<=ids
            scenarios.append(dict(capability=delta.parent.name,scenario=scenario,local_tests=names,
                protocols=refs,acceptance_status='not_run' if refs else 'local_only',
                local_mechanics_do_not_certify_desktop=True))
    assert len(scenarios)==15
    log=ROOT/'.test-data/08-local-final.log'
    content=log.read_text(encoding='utf-8')
    match=re.search(r'(\d+) passed',content)
    assert match and ' failed' not in content
    (OUT/'distribution-local-pytest.log').write_bytes(log.read_bytes())
    smoke=json.loads((OUT/'distribution-wheel-smoke.json').read_bytes())
    full_log=ROOT/'.test-data/08-full.log'
    full_content=full_log.read_text(encoding='utf-8')
    full_match=re.search(r'(\d+) passed',full_content)
    assert full_match and ' failed' not in full_content
    (OUT/'distribution-full-pytest.log').write_bytes(full_log.read_bytes())
    value=dict(schema_version=1,change=change.name,date='2026-10-14',timezone='America/Bogota',
        base_commit=manifest.base_commit,base_implementation_07='af9d645',kit_version=manifest.version,
        local_development_authorized_on='2026-10-13',candidate_sha256=manifest.manifest_sha256,
        completed_tasks=['1.1','1.2','2.1','2.2','2.3','2.4','4.1','4.2'],
        pending_tasks=['3.1','3.2','3.3','3.4','4.3'],change_status='active',
        archive_decision='user_requested_keep_active_until_real_acceptance',implementation_status='complete',
        acceptance_status='pending',certified=False,release_allowed=False,publication_allowed=False,
        next_increment_enabled=False,required_predecessor_runs=144,actual_model_runs=0,
        pytest=dict(local_passed=int(match[1]),log='distribution-local-pytest.log',log_sha256=sha(log.read_bytes()),
            full_passed=int(full_match[1]),full_log='distribution-full-pytest.log',full_log_sha256=sha(full_log.read_bytes()),
            full_run_precedes_additional_local_tests=True),
        wheel_smoke=smoke,assigned_quality_case=dict(id='T22',test='test_T22_personalized_agent_toml_preserves_external_state',
            execution_scope='isolated_local',catalog_status_preserved='not_run'),
        scenarios=scenarios)
    (OUT/'distribution-verification.json').write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    for task in value['completed_tasks']:
        p=change/'tasks.md'
        p.write_text(p.read_text(encoding='utf-8').replace('- [ ] '+task+' ','- [x] '+task+' ',1),encoding='utf-8')
    print(json.dumps(dict(completed_tasks=8,pending_tasks=5,scenarios=15,certified=False)))


if __name__=='__main__': main()
