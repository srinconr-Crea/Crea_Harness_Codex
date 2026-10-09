"""Installed wheel smoke: offline loading, hashes, schemas and no activation."""
import hashlib
import json
import os
import subprocess
from pathlib import Path
from zipfile import ZipFile

root = Path(__file__).resolve().parents[1]
interpreter = root / '.smoke-venv/Scripts/python.exe'
wheel = root / 'dist/crea_local_harness-0.1.0-py3-none-any.whl'
code = '''
import json,sys
from importlib.resources import files
import harness_core,harness_local
from harness_local.quality_resources import load_quality
from harness_core.quality import resolve_practices,definition_report
assert 'site-packages' in harness_local.__file__
assert 'site-packages' in harness_core.__file__
bundle=load_quality()
assert len(bundle.practices.rules)==32
assert len(bundle.tests.cases)==24 and len(bundle.evals.cases)==24
assert any(r.id=='SP-01' for r in resolve_practices(bundle.practices,'pyspark').rules)
assert definition_report(bundle.evals,available_modes=set())['status']=='blocked'
assert all(c.status=='not_run' and c.scores is None for c in bundle.evals.cases)
assert not any(m.startswith(('pyspark','mlflow','databricks')) for m in sys.modules)
print(json.dumps(dict(rules=32,tests=24,evals=24,dataset_sha256=bundle.dataset_sha256,
 manifest_sha256=bundle.manifest_sha256,upstream_commit=bundle.upstream_commit,
 license=bundle.upstream_license,agent_execution='not_run',activation=False)))
'''
environment = dict(os.environ)
environment.pop('PYTHONPATH', None)
run = subprocess.run([str(interpreter), '-I', '-c', code], cwd=root / '.test-data',
                     env=environment, capture_output=True, encoding='utf-8', timeout=30)
assert run.returncode == 0, (run.stdout, run.stderr)
with ZipFile(wheel) as archive:
    assert 'harness_local/quality_kit/vendor/databricks-agent-skills/LICENSE' in archive.namelist()
    assert 'harness_local/quality_kit/vendor/databricks-agent-skills/NOTICE' in archive.namelist()
result = dict(schema_version=1, wheel=wheel.name, wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),
              installed_isolated=True, exit_code=run.returncode, checks=json.loads(run.stdout))
(root / 'docs/evidence/quality-wheel-smoke.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print('Installed quality resources verified; no agents or upstream scripts executed')
