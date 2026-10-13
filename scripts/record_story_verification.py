"""Record observed suite/smoke results and keep real provider acceptance pending."""
import argparse
import hashlib
import json
from pathlib import Path
import re

parser=argparse.ArgumentParser()
parser.add_argument('--pytest-exit-code',type=int,required=True)
args=parser.parse_args()
if args.pytest_exit_code!=0: raise SystemExit('Final suite exit code is not zero.')
root=Path(__file__).resolve().parents[1]
evidence=root/'docs/evidence'
log=evidence/'story-pr-final-pytest.log'
text=log.read_text(encoding='utf-8-sig')
match=re.search(r'(\d+) passed in ([\d.]+)s',text)
if not match or re.search(r'\d+ (?:failed|errors?)',text): raise SystemExit('Suite has not passed.')
wheel=json.loads((evidence/'story-pr-wheel-smoke.json').read_text(encoding='utf-8'))
protocol=json.loads((evidence/'story-pr/protocol-manifest.json').read_text(encoding='utf-8'))
pending=json.loads((evidence/'story-pr/pending-report.json').read_text(encoding='utf-8'))
assert wheel['exit_code']==0 and wheel['installed_isolated']
assert wheel['smoke']['legacy_eval_required_runs']==126
assert protocol['actual_model_runs']==0 and pending['required_runs']==144 and not pending['promotion_allowed']
change=root/'openspec/changes/07-story-and-pr-integrations'
archived=not change.is_dir()
if archived:
    matches=list((root/'openspec/changes/archive').glob('*-07-story-and-pr-integrations'))
    if len(matches)!=1: raise SystemExit('Exactly one archive is required.')
    change=matches[0]
tasks=(change/'tasks.md').read_text(encoding='utf-8-sig')
done=re.findall(r'^- \[x\] (\d\.\d)',tasks,re.M)
remaining=re.findall(r'^- \[ \] (\d\.\d)',tasks,re.M)
assert len(done)==7 and remaining==['2.3','2.5','3.3']
delta=(change/'specs/story-pr-integration/spec.md').read_text(encoding='utf-8-sig')
main=(root/'openspec/specs/story-pr-integration/spec.md').read_text(encoding='utf-8-sig')
assert main.strip()==delta.replace('# Spec Delta','# story-pr-integration Specification').replace('## ADDED Requirements','## Requirements').strip()
old=json.loads((evidence/'observability-evals-verification.json').read_text(encoding='utf-8'))
assert old['pytest']['passed']==439 and old['pending_tasks']==['2.4','3.3'] and not old['exit_criterion_satisfied']
source_paths=['src/harness_core/story.py','src/harness_local/publication.py','src/harness_local/story_providers.py',
    'src/harness_local/cli.py','src/harness_local/evaluation_service.py']
result=dict(schema_version=1,change='07-story-and-pr-integrations',verified_on='2026-10-13',timezone='America/Bogota',
    baseline='54faea5',kit_version='0.1.0',implementation_status='partial',completed_tasks=done,pending_tasks=remaining,
    change_status='archived_with_pending_tasks' if archived else 'active',
    archive_path=change.relative_to(root).as_posix() if archived else None,
    archive_with_pending_authorized=True,pytest=dict(passed=int(match[1]),duration_seconds=float(match[2]),
        exit_code=args.pytest_exit_code,log=log.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest()),
    wheel_smoke=wheel,protocol=protocol,requirements=4,scenarios=10,specs_synced=['story-pr-integration'],spec_sync_exact=True,
    publication_allowed=False,certified=False,next_increment_enabled=False,exit_criterion_satisfied=False,
    reason='real_provider_smoke_and_manual_evaluations_pending',actual_provider_writes=0,actual_model_runs=0,
    deterministic_T20='passed_provider_double',agent_cases={k:'not_run' for k in ['E21','E22','E23']},
    review=dict(independent=True,important_findings=3,transport_attach_contract_clarifications=2,
        regression_tests_passed=True,model_performance_verified=False,real_provider_verified=False),
    source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in source_paths})
(evidence/'story-pr-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=result['pytest']['passed'],completed_tasks=len(done),pending_tasks=remaining,exit_criterion_satisfied=False)))
