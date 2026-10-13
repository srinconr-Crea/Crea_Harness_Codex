"""Fixtures certify runner mechanics, never the model/role behavior they describe."""
import copy
import hashlib
import json

import pytest


def api():
    from harness_core import evaluation
    return evaluation


def bundle():
    from harness_local.quality_resources import load_quality
    return load_quality()


def profile(id='baseline', **changes):
    b = bundle()
    value = dict(schema_version=1, profile_id=id, model='luna', effort='medium',
                 surface='desktop', dataset_sha256=b.dataset_sha256,
                 kit_sha256=b.manifest_sha256, config_sha256='b' * 64,
                 runtime='desktop-captured-version', tools={'harness': '0.1.0'},
                 roles_sha256='c' * 64, practices_sha256='d' * 64)
    value.update(changes)
    return api().EvalProfile.model_validate(value)


def capture(case, p, repetition=1, **changes):
    from harness_core.onboarding_plan import canonical, sha
    payload = {'observed_defects': case.expected.known_defects,
               'checks': [{'check_id': c.id, 'status': 'passed', 'evidence_ref': 'capture1',
                           'annotator': 'operator', 'annotation_kind': 'human',
                           'reason': 'Protocol reviewed'} for c in case.expected.checks]}
    # All captures in tests are deliberately marked simulated.
    value = dict(schema_version=1, run_id=f'{case.id}-{p.profile_id}-{repetition}',
                 case_id=case.id, role=case.role, profile_sha256=sha(canonical(p.model_dump())),
                 repetition=repetition, surface=p.surface, mode='manual', status='passed',
                 observed_at='2026-10-13T10:00:00Z', duration_ms=20.0,
                 artifact_ref='capture1', artifact_sha256=sha(canonical(payload)),
                 output=payload, simulated=True)
    value.update(changes)
    return api().EvalRun.model_validate(value)


def batch(cases=None):
    q = api(); b = bundle(); p = profile()
    cases = cases or [next(c for c in b.evals.cases if c.id == 'E14')]
    runs = [capture(c, p, n) for c in cases for n in range(1, 4)]
    return b, p, cases, runs


def test_per_check_scorer_detects_false_findings_and_critical_misses():
    q = api(); b, p, cases, runs = batch(); c = cases[0]
    scores, findings = q.score_run(c, runs[0])
    assert all(s.status == 'passed' for s in scores)
    bad = runs[0].model_dump()
    bad['output']['observed_defects'] = ['duplicate_dimension']
    from harness_core.onboarding_plan import canonical, sha
    bad['artifact_sha256'] = sha(canonical(bad['output']))
    scores, findings = q.score_run(c, q.EvalRun.model_validate(bad))
    assert findings['false_positives'] == ['duplicate_dimension']
    assert any(s.critical and s.status == 'failed' for s in scores)


@pytest.mark.parametrize('state', ['blocked', 'not_run', 'failed'])
def test_state_cannot_be_laundered_by_passing_annotations(state):
    q = api(); b, p, cases, runs = batch()
    value = runs[0].model_dump(); value['status'] = state
    scores, _ = q.score_run(cases[0], q.EvalRun.model_validate(value))
    assert all(s.status == state for s in scores)


def test_missing_annotation_or_uncalibrated_judge_never_passes():
    q = api(); b, p, cases, runs = batch()
    from harness_core.onboarding_plan import canonical, sha
    value = runs[0].model_dump(); value['output']['checks'] = []
    value['artifact_sha256'] = sha(canonical(value['output']))
    scores, _ = q.score_run(cases[0], q.EvalRun.model_validate(value))
    assert all(s.status == 'not_run' for s in scores)
    value = runs[0].model_dump(); value['output']['checks'][0]['annotation_kind'] = 'llm'
    value['artifact_sha256'] = sha(canonical(value['output']))
    scores, _ = q.score_run(cases[0], q.EvalRun.model_validate(value))
    assert scores[0].status == 'blocked'


def test_simulated_repetitions_cannot_promote_desktop():
    q = api(); b, p, cases, runs = batch()
    result = q.promotion_report(b.evals, [p], runs, milestone=6, purpose='promotion')
    assert result['status'] == 'blocked' and not result['promotion_allowed']
    assert result['profiles'][0]['pending'] > 0
    assert result['profiles'][0]['simulated_runs'] == 3
    assert result['certified'] is False


def test_missing_repetition_wrong_surface_and_stale_configuration_fail():
    q = api(); b, p, cases, runs = batch()
    result = q.promotion_report(b.evals, [p], runs[:2], milestone=6, purpose='promotion')
    assert result['status'] == 'blocked'
    value = runs[0].model_dump(); value['surface'] = 'cli'
    with pytest.raises(ValueError, match='execution_surface_mismatch'):
        q.promotion_report(b.evals, [p], [q.EvalRun.model_validate(value)], milestone=6, purpose='promotion')
    value = runs[0].model_dump(); value['profile_sha256'] = 'a' * 64
    with pytest.raises(ValueError, match='unknown_profile'):
        q.promotion_report(b.evals, [p], [q.EvalRun.model_validate(value)], milestone=6, purpose='promotion')


def test_milestone_selection_and_holdout_reserved_for_promotion():
    q = api(); b = bundle()
    selected, future = q.select_cases(b.evals, milestone=6, purpose='promotion')
    assert {'E13', 'E14', 'E15', 'E16', 'E17', 'E18', 'E20'} <= {c.id for c in selected}
    assert {c.id for c in future} == {'E21', 'E22', 'E23'}
    golden, _ = q.select_cases(b.evals, milestone=6, purpose='development')
    assert all(c.split == 'golden' for c in golden)
    with pytest.raises(ValueError, match='holdout_reserved'):
        q.promotion_report(b.evals, [profile()], [capture(next(c for c in selected if c.id == 'E14'), profile())],
                           milestone=6, purpose='development')


def test_profile_comparison_requires_same_dataset_kit_runtime_and_tools():
    q = api(); b = bundle(); p = profile()
    for changes in ({'dataset_sha256': 'f' * 64}, {'runtime': 'different-runtime'},
                    {'tools': {'harness': '0.2.0'}}, {'kit_sha256': 'f' * 64}):
        with pytest.raises(ValueError, match='incomparable_profiles'):
            q.promotion_report(b.evals, [p, profile('candidate', **changes)], [], milestone=6, purpose='promotion')


def test_artifact_tampering_and_duplicate_checks_rejected():
    q = api(); b, p, cases, runs = batch()
    value = runs[0].model_dump(); value['output']['observed_defects'] = ['new_defect']
    with pytest.raises(ValueError, match='artifact_hash_mismatch'):
        q.EvalRun.model_validate(value)
    value = runs[0].model_dump(); value['output']['checks'] *= 2
    with pytest.raises(ValueError):
        q.EvalRun.model_validate(value)


def test_missing_desktop_automation_returns_blocked_without_api_calls():
    from harness_local.evaluation_service import dispatch
    p = profile()
    result, code = dispatch('run', dict(schema_version=1, milestone=6, purpose='promotion',
        profiles=[p.model_dump()], runs=[], budget_runs=63, execution_mode='automatic'))
    assert code == 1 and result['reason'] == 'supported_desktop_automation_unavailable'


def test_budget_and_duplicate_repetitions_rejected():
    q = api(); b, p, cases, runs = batch()
    with pytest.raises(ValueError, match='duplicate_repetition'):
        q.promotion_report(b.evals, [p], [runs[0], runs[0]], milestone=6, purpose='promotion')
    from harness_local.evaluation_service import dispatch
    with pytest.raises(ValueError, match='eval_budget_exceeded'):
        dispatch('run', dict(schema_version=1, milestone=6, purpose='promotion',
            profiles=[p.model_dump()], runs=[], budget_runs=1, execution_mode='manual'))


def reviewed_batch():
    """Explicit unit-test representation of manual receipts, not model executions."""
    q = api(); b = bundle()
    p = profile(configuration_evidence_ref='operator-config-receipt')
    cases, _ = q.select_cases(b.evals, milestone=6, purpose='promotion')
    runs = [capture(c, p, n, simulated=False) for c in cases for n in range(1, 4)]
    return b, p, cases, runs


def test_complete_manual_receipts_gate_and_single_critical_regression():
    q = api(); b, p, cases, runs = reviewed_batch()
    result = q.promotion_report(b.evals, [p], runs, milestone=6, purpose='promotion')
    assert result['promotion_allowed'] and result['status'] == 'passed'
    assert not result['certified'] and not result['publication_allowed']
    assert result['profiles'][0]['duration_variance_ms2'] == 0
    from harness_core.onboarding_plan import canonical, sha
    value = runs[0].model_dump(); value['output']['checks'][0]['status'] = 'failed'
    value['artifact_sha256'] = sha(canonical(value['output']))
    runs[0] = q.EvalRun.model_validate(value)
    result = q.promotion_report(b.evals, [p], runs, milestone=6, purpose='promotion')
    assert not result['promotion_allowed']
    assert 0.9 < result['profiles'][0]['critical_pass_rate'] < 1


def test_missing_noncritical_annotation_blocks_even_above_ninety_percent():
    q = api(); b, p, cases, runs = reviewed_batch()
    from harness_core.onboarding_plan import canonical, sha
    index = next(i for i, run in enumerate(runs) if run.case_id == 'E14')
    value = runs[index].model_dump()
    value['output']['checks'] = [c for c in value['output']['checks'] if c['check_id'] != 'E14-C2']
    value['artifact_sha256'] = sha(canonical(value['output']))
    runs[index] = q.EvalRun.model_validate(value)
    result = q.promotion_report(b.evals, [p], runs, milestone=6, purpose='promotion')
    assert result['profiles'][0]['noncritical_pass_rate'] >= 0.9
    assert result['profiles'][0]['pending'] == 1
    assert not result['promotion_allowed']


def test_two_profiles_compare_same_model_and_effort_without_claiming_model_runs():
    q = api(); b, p, cases, runs = reviewed_batch()
    second = profile('candidate', configuration_evidence_ref='operator-config-receipt')
    runs += [capture(c, second, n, simulated=False) for c in cases for n in range(1, 4)]
    result = q.promotion_report(b.evals, [p, second], runs, milestone=6, purpose='promotion')
    assert result['comparable'] and result['promotion_allowed']
    assert len(result['profiles']) == 2
    assert all(row['model'] == 'luna' and row['effort'] == 'medium' for row in result['profiles'])


def test_profile_without_configuration_evidence_and_automatic_receipts_blocked():
    q = api(); b, p, cases, runs = reviewed_batch()
    from harness_core.onboarding_plan import canonical, sha
    unverified = profile()
    digest = sha(canonical(unverified.model_dump()))
    runs = [q.EvalRun.model_validate(dict(r.model_dump(), profile_sha256=digest)) for r in runs]
    assert not q.promotion_report(b.evals, [unverified], runs, milestone=6, purpose='promotion')['promotion_allowed']
    runs = [q.EvalRun.model_validate(dict(r.model_dump(), mode='automatic', profile_sha256=sha(canonical(p.model_dump())))) for r in runs]
    assert not q.promotion_report(b.evals, [p], runs, milestone=6, purpose='promotion')['promotion_allowed']


def test_unimplemented_milestone_cannot_be_selected_in_service():
    from harness_local.evaluation_service import dispatch
    for milestone in (8,):
        with pytest.raises(ValueError, match='milestone_not_available'):
            dispatch('report', dict(schema_version=1, milestone=milestone, purpose='promotion',
                profiles=[profile().model_dump()], runs=[], budget_runs=1000, execution_mode='manual'))


def test_optional_duration_remains_null_without_measurement():
    q = api(); b, p, cases, runs = reviewed_batch()
    runs = [q.EvalRun.model_validate(dict(r.model_dump(), duration_ms=None)) for r in runs]
    result = q.promotion_report(b.evals, [p], runs, milestone=6, purpose='promotion')
    assert result['profiles'][0]['duration_mean_ms'] is None
    assert result['profiles'][0]['duration_variance_ms2'] is None


def test_report_cannot_bypass_batch_budget():
    from harness_local.evaluation_service import dispatch
    b, p, cases, runs = reviewed_batch()
    value = dict(schema_version=1, milestone=6, purpose='promotion',
                 profiles=[p.model_dump()], runs=[r.model_dump() for r in runs],
                 budget_runs=1, execution_mode='manual')
    for action in ('run', 'report'):
        with pytest.raises(ValueError, match='eval_budget_exceeded'):
            dispatch(action, value)
