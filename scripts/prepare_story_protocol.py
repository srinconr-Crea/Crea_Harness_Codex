"""Extend the offline evaluation protocol to 07 without modifying 06 evidence."""
import json
from pathlib import Path

from harness_local.evaluation_service import dispatch

root = Path(__file__).resolve().parents[1]
directory = root/'docs/evidence/story-pr'
directory.mkdir(exist_ok=True)
request = json.loads((root/'docs/evidence/observability-evals/pending-batch.json').read_text(encoding='utf-8'))
request.update(milestone=7, budget_runs=144)
report, code = dispatch('report', request)
assert code == 1 and report['required_runs'] == 144 and not report['promotion_allowed']
assert not request['runs'] and all(row['status']=='not_run' for p in report['profiles'] for row in p['matrix'])
for name, value in [('pending-batch.json',request),('pending-report.json',report)]:
    (directory/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
manifest = dict(schema_version=1,actual_model_runs=0,required_runs=144,previous_pending_runs=126,
    provider_cases=['E21','E22','E23'],provider_pending_runs=18,requested_model='luna',requested_effort='medium',
    effective_model_verified=False,publication_allowed=False,next_increment_enabled=False,
    remote_write_smoke=dict(status='blocked',reason='required_evaluations_pending_and_synthetic_destination_not_selected'),
    archive_with_pending_authorized_on='2026-10-13')
(directory/'protocol-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps(manifest))
