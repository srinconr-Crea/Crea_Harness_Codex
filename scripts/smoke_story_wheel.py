"""Installed wheel contracts/resources and preview with no authentication or writes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
interpreter = root/'.smoke-venv/Scripts/python.exe'
wheel = root/'dist/crea_local_harness-0.1.0-py3-none-any.whl'
code = r'''
import contextlib, hashlib, io, json, sys
from importlib.resources import files
from harness_core.story import MODELS
from harness_core.hu import HuRun, Candidate, PlanRevision, ApprovalRecord
from harness_local.evaluation_service import dispatch
from harness_local.publication import PublicationRequest, preview, evaluation_gate
from harness_local.cli import main
for model in (*MODELS, PublicationRequest, HuRun, Candidate, PlanRevision, ApprovalRecord):
    assert json.loads(files('harness_core').joinpath('schemas/'+model.__name__.lower()+'.schema.json').read_bytes())==model.model_json_schema()
root=files('harness_local').joinpath('story_kit')
manifest=json.loads(root.joinpath('manifest.json').read_bytes())
for name, digest in manifest['files'].items():
    assert hashlib.sha256(root.joinpath(name).read_bytes()).hexdigest()==digest
request=PublicationRequest.model_validate(json.loads(root.joinpath('preview.json').read_bytes()))
result=preview(request.intent)
assert result['draft'] and not result['publication_allowed'] and result['publication_gate']=='blocked'
assert evaluation_gate(json.loads(open(sys.argv[1],encoding='utf-8').read()))=='required_evaluations_blocked'
legacy=json.loads(open(sys.argv[1],encoding='utf-8').read()); legacy.update(milestone=6,budget_runs=126)
old,oldcode=dispatch('report',legacy)
assert oldcode==1 and old['required_runs']==126 and not old['promotion_allowed']
output=io.StringIO()
with contextlib.redirect_stdout(output):
    code=main(['pr','preview','--input',str(root.joinpath('preview.json')),'--json'])
assert code==0 and json.loads(output.getvalue())['publication_allowed'] is False
output=io.StringIO()
with contextlib.redirect_stdout(output):
    legacy_code=main(['init','--dry-run','--path','missing-story-smoke-target',
        '--policy','missing-policy.json','--binding','missing-binding.json','--json'])
assert legacy_code==2 and json.loads(output.getvalue())['checks'][0]['code']=='target_not_found'
assert not any(name.startswith(('pyspark','mlflow','databricks','openai')) for name in sys.modules)
print(json.dumps(dict(contracts=7,resources=len(manifest['files']),preview='partial',evaluation_gate='blocked',
    legacy_hu_contracts=4,legacy_eval_required_runs=126,legacy_cli_preview='preserved',
    remote_writes=0,actual_model_runs=0,global_activation=False,certified=False)))
'''
environment = dict(os.environ); environment.pop('PYTHONPATH',None)
run = subprocess.run([str(interpreter),'-I','-c',code,str(root/'docs/evidence/story-pr/pending-batch.json')],
    cwd=root/'.test-data',env=environment,capture_output=True,text=True,timeout=30)
assert run.returncode == 0, (run.stdout,run.stderr)
result = dict(schema_version=1,wheel=wheel.name,wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),
    installed_isolated=True,exit_code=run.returncode,smoke=json.loads(run.stdout))
(root/'docs/evidence/story-pr-wheel-smoke.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
