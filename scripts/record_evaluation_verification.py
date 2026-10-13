"""Record observed test/smoke evidence; refuse to invent a final suite result."""
import hashlib
import json
from pathlib import Path
import re


root = Path(__file__).resolve().parents[1]
evidence = root / 'docs/evidence'
log = evidence / 'observability-evals-final-pytest.log'
text = log.read_text(encoding='utf-8-sig')
match = re.search(r'(\d+) passed in ([\d.]+)s', text)
if not match or re.search(r'\d+ (?:failed|errors?)', text):
    raise SystemExit('Final suite has not passed; do not record completion.')
wheel = json.loads((evidence / 'observability-evals-wheel-smoke.json').read_text(encoding='utf-8'))
protocol = json.loads((evidence / 'observability-evals/protocol-manifest.json').read_text(encoding='utf-8'))
pending = json.loads((evidence / 'observability-evals/pending-report.json').read_text(encoding='utf-8'))
assert wheel['exit_code'] == 0 and wheel['installed_isolated']
assert protocol['actual_model_runs'] == 0 and pending['status'] == 'blocked'
assert not pending['promotion_allowed'] and not protocol['next_increment_enabled']
tasks = (root / 'openspec/changes/06-observability-and-agent-evals/tasks.md').read_text(encoding='utf-8-sig')
done = re.findall(r'^- \[x\] (\d\.\d)', tasks, re.M)
remaining = re.findall(r'^- \[ \] (\d\.\d)', tasks, re.M)
assert len(done) == 9 and remaining == ['2.4', '3.3']
for name in ('agent-evaluation', 'development-observability'):
    delta = (root / f'openspec/changes/06-observability-and-agent-evals/specs/{name}/spec.md').read_text(encoding='utf-8-sig')
    main = (root / f'openspec/specs/{name}/spec.md').read_text(encoding='utf-8-sig')
    expected = delta.replace('# Spec Delta', f'# {name} Specification').replace('## ADDED Requirements', '## Requirements')
    assert main.strip() == expected.strip(), 'Spec sync mismatch: ' + name
source_paths = ['src/harness_core/observability.py', 'src/harness_core/evaluation.py',
                'src/harness_local/observability_service.py', 'src/harness_local/evaluation_service.py',
                'src/harness_local/cli.py']
result = dict(schema_version=1, change='06-observability-and-agent-evals',
    verified_on='2026-10-13', timezone='America/Bogota', baseline='75c1bfc', kit_version='0.1.0',
    implementation_status='partial', completed_tasks=done, pending_tasks=remaining,
    pytest=dict(passed=int(match[1]), duration_seconds=float(match[2]),
                log=log.name, log_sha256=hashlib.sha256(log.read_bytes()).hexdigest()),
    wheel_smoke=wheel, protocol=protocol,
    specs_synced=['agent-evaluation', 'development-observability'],
    spec_sync_exact=True, requirements=5, scenarios=10,
    promotion_allowed=False, certified=False, next_increment_enabled=False,
    source_sha256={p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in source_paths},
    review=dict(independent=True, findings=2, fixes_verified_red_green=True,
                open_code_findings=0, model_performance_verified=False),
    exit_criterion_satisfied=False, reason='manual_evaluations_not_run')
(evidence / 'observability-evals-verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(passed=result['pytest']['passed'], completed_tasks=len(done),
                     pending_tasks=remaining, exit_criterion_satisfied=False)))
