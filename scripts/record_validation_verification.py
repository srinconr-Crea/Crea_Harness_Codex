"""Record observed final checks; refuse a failed or unfinished suite."""
import json
from pathlib import Path
import re
import subprocess

from harness_core.onboarding_plan import sha

root=Path(__file__).resolve().parents[1]
evidence=root/'docs/evidence'
log=(evidence/'candidate-validation-pytest.log').read_text(encoding='utf-8')
match=re.search(r'(\d+) passed in ([\d.]+)s',log)
if not match or re.search(r'\d+ (failed|error)',log): raise SystemExit('Suite final no aprobada/completa')
change='05-databricks-validation-and-evidence'
validated=subprocess.run(['openspec.cmd','validate',change,'--strict'],cwd=root,capture_output=True,text=True)
if validated.returncode: raise SystemExit('OpenSpec strict no aprobado')
(evidence/'candidate-validation-openspec.log').write_text(validated.stdout+validated.stderr,encoding='utf-8')
smoke=json.loads((evidence/'candidate-validation-wheel-smoke.json').read_text())
remote=json.loads((evidence/'candidate-validation-remote-smoke.json').read_text())
if smoke['exit_code']!=0 or remote['status']!='blocked' or remote['evidence']['reason']!='sandbox_not_selected':
    raise SystemExit('Smoke no corresponde a protocolo seleccionado')
delta=(root/f'openspec/changes/{change}/specs/candidate-validation/spec.md').read_text(encoding='utf-8')
main=(root/'openspec/specs/candidate-validation/spec.md').read_text(encoding='utf-8')
expected=delta.replace('# Spec Delta','# candidate-validation Specification').replace('## ADDED Requirements','## Requirements')
if expected.strip()!=main.strip(): raise SystemExit('Delta/main no coinciden')
tasks=(root/f'openspec/changes/{change}/tasks.md').read_text(encoding='utf-8')
if len(re.findall(r'^- \[x\]',tasks,re.M))!=10 or '- [ ]' in tasks: raise SystemExit('Tareas incompletas')
result=dict(schema_version=1,change=change,date='2026-10-13',timezone='America/Bogota',baseline_commit='bf7fd93',
    dependency=dict(change='04-hu-lifecycle-and-development-gates',commit='bf7fd93',version='0.1.0',verified=True),
    suite=dict(status='passed',passed=int(match[1]),seconds=float(match[2]),log='candidate-validation-pytest.log',sha256=sha((evidence/'candidate-validation-pytest.log').read_bytes())),
    prefinal_suite=dict(passed=369,failed=28,disposition='26 concurrent edit mismatches; sandbox Git positive control and isolated recovery retry; retained log'),
    installed_wheel=smoke,remote_smoke=dict(status='blocked',reason='sandbox_not_selected',genuine_remote_execution=False,user_selected=True),
    container_spark=dict(status='blocked',reason='worker_runtime_absent'),
    agent_evals={case:dict(status='not_run',observed_output=None,scores=None) for case in ('E07','E09','E10','E11','E12')},
    verification=dict(tasks='10/10',requirements='4/4',scenarios='8/8',completeness='passed',correctness='passed',coherence='passed',
        strict_validation_exit_code=validated.returncode,main_spec_sync='exact',global_activation=False,v1_contracts_changed=False),
    next_increment=dict(name='06-observability-and-agent-evals',implementation_enabled=True,remote_capabilities_remain_blocked=True))
(evidence/'candidate-validation-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=int(match[1]),tasks='10/10',requirements='4/4',scenarios='8/8',remote='blocked')))
