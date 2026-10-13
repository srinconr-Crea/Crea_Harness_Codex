"""Prepare a pending, offline protocol. Never execute models or populate passed scores."""
import json
from pathlib import Path

from harness_core.evaluation import EvalProfile, select_cases
from harness_core.onboarding_plan import canonical, sha
from harness_local.quality_resources import load_quality
from harness_local.evaluation_service import dispatch


root = Path(__file__).resolve().parents[1]
quality = load_quality()
roles = (root / 'src/harness_local/desktop_kit/roles.json').read_bytes()
practices = (root / 'src/harness_local/quality_kit/practices.json').read_bytes()
# User chose Luna/medium for both. Exact effective model id/version must be captured
# from Desktop before any promotion. No latest-model substitution or API engine.
profiles = []
for name in ('baseline', 'candidate'):
    config = dict(model='luna', effort='medium', profile_id=name, roles_sha256=sha(roles),
                  practices_sha256=sha(practices))
    profiles.append(EvalProfile(schema_version=1, profile_id=name, model='luna', effort='medium',
        surface='desktop', dataset_sha256=quality.dataset_sha256, kit_sha256=quality.manifest_sha256,
        config_sha256=sha(canonical(config)), runtime='desktop_pending_effective_version',
        tools={'harness': '0.1.0'}, roles_sha256=sha(roles), practices_sha256=sha(practices),
        configuration_evidence_ref=None).model_dump())
request = dict(schema_version=1, milestone=6, purpose='promotion', profiles=profiles,
               runs=[], budget_runs=126, execution_mode='manual')
directory = root / 'docs/evidence/observability-evals'
directory.mkdir(exist_ok=True)
(directory / 'pending-batch.json').write_text(json.dumps(request, indent=2) + '\n', encoding='utf-8')
report, code = dispatch('report', request)
assert code == 1 and not report['promotion_allowed']
(directory / 'pending-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
selected, future = select_cases(quality.evals, milestone=6, purpose='promotion')
manifest = dict(schema_version=1, status='not_run', actual_model_runs=0,
    selected_cases=[c.id for c in selected], future_cases=[c.id for c in future],
    profiles=[p['profile_id'] for p in profiles], repetitions=3, required_runs=126,
    requested_model='luna', requested_effort='medium',
    effective_model_verified=False, configuration_evidence_ref=None,
    dataset_sha256=quality.dataset_sha256, kit_sha256=quality.manifest_sha256,
    holdout_reserved_for_promotion=True, next_increment_enabled=False)
(directory / 'protocol-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print(json.dumps(manifest))
