"""Use an installed candidate in a separate venv, without source-path imports."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
wheel=ROOT/'dist/crea_local_harness-0.1.0-py3-none-any.whl'
interpreter=ROOT/'.test-data/d2/Scripts/python.exe'
code=r'''
import contextlib,io,json,sys
from importlib.resources import files
from harness_core.distribution import MODELS,PilotReport
from harness_local.distribution import candidate_manifest,bootstrap,release_gate
from harness_local.cli import main
from harness_local.quality_resources import load_quality
from harness_local.desktop_resources import load_desktop
for model in MODELS:
    assert json.loads(files('harness_core').joinpath('schemas/'+model.__name__.lower()+'.schema.json').read_bytes())==model.model_json_schema()
manifest=candidate_manifest()
assert not manifest.certified and not manifest.release_allowed
assert bootstrap(detect=lambda _:None)[0]['login']=='pending'
pilot=PilotReport(schema_version=1,candidate_sha256=manifest.manifest_sha256,implementation_status='complete',receipts=[])
result,code=release_gate(pilot)
assert code==1 and not result['release_allowed'] and len(result['pending'])>=11
for args in (['bootstrap','--json'],['release','candidate','--json']):
    out=io.StringIO()
    with contextlib.redirect_stdout(out): assert main(args)==0
    assert json.loads(out.getvalue())['certified'] is False
assert len(load_desktop().roles)==8
assert load_quality().practices.version
assert not any(name.startswith(('openai','databricks','pyspark','mlflow')) for name in sys.modules)
print(json.dumps(dict(contracts=len(MODELS),resources=len(manifest.resources),dependencies=len(manifest.dependencies),
    bootstrap='partial',release_gate='blocked',certified=False,release_allowed=False,
    actual_model_runs=0,remote_writes=0,second_environment_verified=False,legacy_resources='preserved')))
'''
run=subprocess.run([str(interpreter),'-I','-c',code],cwd=ROOT/'.test-data',capture_output=True,text=True,timeout=30)
assert run.returncode==0,(run.stdout,run.stderr)
result=dict(schema_version=1,wheel=wheel.name,wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),
    installed_isolated=True,exit_code=run.returncode,smoke=json.loads(run.stdout))
(ROOT/'docs/evidence/distribution-wheel-smoke.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
