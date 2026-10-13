"""Synthetic, unauthorized examples for the independent validation contracts."""
import json
from pathlib import Path
from harness_local.validation import select_plan
from harness_core.validation import ValidationRequest,WorkerRuntime,SandboxTarget,make_evidence
from harness_core.onboarding_plan import canonical,sha

root=Path(__file__).resolve().parents[1]/'docs/examples/validation'
root.mkdir(parents=True,exist_ok=True)
p=select_plan(client_id='synthetic',run_id='example',attempt=1,candidate_sha256='a'*64,
    plan_revision=1,technologies=['python'],impacts=['logic'])
r=ValidationRequest(schema_version=1,plan_sha256=p.plan_sha256,test_id='python-unit',client_id=p.client_id,
    run_id=p.run_id,attempt=1,candidate_sha256=p.candidate_sha256,plan_revision=1,practice_pack_sha256=p.practice_pack_sha256,
    data_sha256=sha(canonical([{'args':[['0.10','0.20',None]]},{'args':[[]]}])),runtime='python-3.13',
    runtime_sha256='e'*64,tool_sha256='d'*64,request_key='example',command=['docker','run','pinned-worker'])
runtime=WorkerRuntime(schema_version=1,image='python@sha256:'+'e'*64,runtime='python-3.13',python_version='3.13.7',authorized=False)
target=SandboxTarget(schema_version=1,profile='SELECTED',host='https://sandbox.example.invalid',
    caller_identity='operator@example.invalid',execution_identity='runner@example.invalid',job_id=1,task_key='validate',
    runtime='15.4.x-scala2.12',volume='/Volumes/sandbox/test/fixtures',resources=['/Workspace/sandbox/validate'],
    modes=['sql','notebook','delta','job'],job_settings_sha256='f'*64,notebook_sha256='e'*64,authorized=False,synthetic=True)
e=make_evidence(r,'blocked',reason='worker_runtime_absent')
for item in (p,r,e,runtime,target):
    (root/(type(item).__name__.lower()+'.json')).write_text(json.dumps(item.model_dump(),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
remote_plan=select_plan(client_id='synthetic',run_id='remote-smoke',attempt=1,candidate_sha256='a'*64,
    plan_revision=1,technologies=['sql'],impacts=['logic'])
remote_request=ValidationRequest(**(r.model_dump()|dict(plan_sha256=remote_plan.plan_sha256,
    test_id='sql-semantic',run_id=remote_plan.run_id,runtime='not-selected',command=['harness','validate','remote'])))
remote=dict(schema_version=1,plan=remote_plan.model_dump(),request=remote_request.model_dump(),
    target=None,state_dir=str(root.parent.parent.parent/'.test-data/remote-smoke-state'),mode='sql',expected={'rows':3,'sum':'30.00'})
(root/'remote-blocked.json').write_text(json.dumps(remote,indent=2)+'\n',encoding='utf-8')
