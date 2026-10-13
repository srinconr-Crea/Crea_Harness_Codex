"""Smoke independent contracts/CLI/passive resources from the installed wheel."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[1]
interpreter=root/'.smoke-venv/Scripts/python.exe'
wheel=root/'dist/crea_local_harness-0.1.0-py3-none-any.whl'
code=r'''
import json,sys
from importlib.resources import files
from harness_local.validation_resources import resources
from harness_local.validation import select_plan
from harness_core.validation import ValidationPlan,ValidationRequest,ValidationEvidence,SandboxTarget,WorkerRuntime,validation_gate
p=select_plan(client_id='synthetic',run_id='wheel',attempt=1,candidate_sha256='a'*64,plan_revision=1,technologies=['python'],impacts=['logic'])
assert validation_gate(p,[])['status']=='blocked'
assert all(t.layer in ('L0','L1') for t in p.tests)
templates=resources()
assert set(templates)=={'python_total.py','spark_total.py','spark_worker.py','synthetic_notebook.py'}
for model in (ValidationPlan,ValidationRequest,ValidationEvidence,SandboxTarget,WorkerRuntime):
    json.loads(files('harness_core').joinpath('schemas/'+model.__name__.lower()+'.schema.json').read_bytes())
assert not any(name.startswith(('pyspark','mlflow','databricks','sqlglot')) for name in sys.modules)
print(json.dumps(dict(contracts=5,passive_templates=4,missing_evidence='blocked',remote_smoke='blocked',global_activation=False)))
'''
environment=dict(os.environ); environment.pop('PYTHONPATH',None)
run=subprocess.run([str(interpreter),'-I','-c',code],cwd=root/'.test-data',env=environment,
    capture_output=True,text=True,timeout=30)
assert run.returncode==0,(run.stdout,run.stderr)
result=dict(schema_version=1,wheel=wheel.name,wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),
    installed_isolated=True,exit_code=run.returncode,smoke=json.loads(run.stdout))
(root/'docs/evidence/candidate-validation-wheel-smoke.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
