"""Verify installed, isolated eval/usage contracts and commands without model calls."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


root = Path(__file__).resolve().parents[1]
interpreter = root / '.smoke-venv/Scripts/python.exe'
wheel = root / 'dist/crea_local_harness-0.1.0-py3-none-any.whl'
code = r'''
import contextlib, io, json, sys
from importlib.resources import files
from harness_core.observability import ActivityEvent, UsageObservation, desktop_usage
from harness_core.evaluation import EvalProfile, EvalRun, EvalScore
from harness_local.evaluation_service import EvalInput
from harness_local.observability_service import UsageInput
from harness_local.cli import main
for model in (ActivityEvent, UsageObservation, EvalProfile, EvalRun, EvalScore, EvalInput, UsageInput):
    schema = json.loads(files('harness_core').joinpath('schemas/'+model.__name__.lower()+'.schema.json').read_bytes())
    assert schema == model.model_json_schema()
observation = desktop_usage(client_id='synthetic', hu_id='HU1', attempt=1, observed_at='2026-10-13T00:00:00Z')
assert observation.cost_usd is None and observation.reason
output = io.StringIO()
with contextlib.redirect_stdout(output):
    code = main(['eval', 'report', '--input', sys.argv[1], '--json'])
report = json.loads(output.getvalue())
assert code == 1 and report['status'] == 'blocked' and report['required_runs'] == 126
assert not report['promotion_allowed'] and not report['certified']
assert not any(name.startswith(('pyspark','mlflow','databricks','openai')) for name in sys.modules)
print(json.dumps(dict(contracts=7, required_runs=126, actual_model_runs=0, pending_gate='blocked',
                     usage='unavailable', global_activation=False, certified=False)))
'''
environment = dict(os.environ)
environment.pop('PYTHONPATH', None)
run = subprocess.run([str(interpreter), '-I', '-c', code,
                      str(root / 'docs/evidence/observability-evals/pending-batch.json')],
                     cwd=root / '.test-data', env=environment, capture_output=True,
                     text=True, timeout=30)
assert run.returncode == 0, (run.stdout, run.stderr)
result = dict(schema_version=1, wheel=wheel.name,
              wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),
              installed_isolated=True, exit_code=run.returncode, smoke=json.loads(run.stdout))
(root / 'docs/evidence/observability-evals-wheel-smoke.json').write_text(
    json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
