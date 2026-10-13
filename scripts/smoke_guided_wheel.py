"""Installed guided onboarding smoke with disposable synthetic client only."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid

root = Path(__file__).resolve().parents[1]
interpreter = root / '.smoke-venv/Scripts/python.exe'
wheel = root / 'dist/crea_local_harness-0.1.0-py3-none-any.whl'
scratch = root / '.test-data' / ('guided-wheel-' + uuid.uuid4().hex)
scratch.mkdir(parents=True)
code = '''
import json,sys,subprocess
from pathlib import Path
from importlib.resources import files
import harness_core,harness_local
from harness_core.guided import QuestionnaireDraft,GuidedRequest
from harness_core.onboarding_plan import sha
from harness_local.guided_resources import resources
from harness_local.guided_onboarding import preview,apply,recover
from harness_local.diagnostics import Check
assert 'site-packages' in harness_local.__file__ and 'site-packages' in harness_core.__file__
bundle=resources()
template=QuestionnaireDraft.model_validate(json.loads(bundle['complete-template.json']))
base=Path(sys.argv[1]); target=base/'client'; target.mkdir()
subprocess.run(['git','init','--initial-branch=develop',str(target)],check=True,capture_output=True)
subprocess.run(['git','-C',str(target),'remote','add','origin','https://github.com/demo/alpha.git'],check=True,capture_output=True)
original=b'# Synthetic custom instructions\\r\\n'; (target/'AGENTS.md').write_bytes(original)
policy=base/'policy.json'
policy.write_text(json.dumps(dict(schema_version=1,policy_id='synthetic',client_id='alpha',repository='demo/alpha',base_branch='develop',branch_prefix='codex/',read_only_paths=[],denied_paths=['private/'],max_files=64,max_bytes=2000000)))
value=template.model_dump()
for key,item in dict(target_path=str(target),policy_path=str(policy),binding_path=str(base/'binding.json'),state_dir=str(base/'state/alpha/checkout')).items(): value['answers'][key]['value']=item
draft=QuestionnaireDraft.model_validate(value)
def ready(name): return Check(name,'ready','synthetic','synthetic local probe')
def snapshot(): return {str(p.relative_to(base)):sha(p.read_bytes()) for p in base.rglob('*') if p.is_file()}
before=snapshot(); report,exit=preview(draft,probe_fn=ready)
assert exit==0 and not report['plan']['init_v1']['applicable'] and snapshot()==before
plan=base/'plan.json'; preview(draft,probe_fn=ready,plan_out=plan)
report,exit=apply(plan,stage='prepare',probe_fn=ready)
assert exit==0 and report['prepared'] and not report['certified'] and report['remote_not_checked']
assert (target/'.harness/context.md').exists() and (target/'.agents/skills/harness-client-onboarding/SKILL.md').exists()
assert (base/'binding.json.tools.json').exists()
report,exit=apply(plan,stage='integrate',probe_fn=ready)
assert exit==0 and report['stages']['integrate']=='completed' and (target/'AGENTS.md').read_bytes().startswith(b'# Synthetic custom instructions')
after=snapshot(); assert apply(plan,stage='prepare',probe_fn=ready)[0]['idempotent'] and snapshot()==after
recover(plan,stage='integrate',apply_changes=True); report,exit=recover(plan,stage='prepare',apply_changes=True)
assert exit==0 and (target/'AGENTS.md').read_bytes()==original and not (base/'binding.json').exists()
for name in ('clientdevelopmentconfig','clienttoolbinding','questionnairedraft','guidedrequest','compositepreparationplan','guidedonboardingplan','onboardingrun','certificationinput'): json.loads(files('harness_core').joinpath('schemas/'+name+'.schema.json').read_bytes())
assert not any(m.startswith(('pyspark','mlflow','databricks')) for m in sys.modules)
print(json.dumps(dict(checks=18,schemas=8,dependency='verified-supervised',client='synthetic',stages=['prepare','integrate','recover'],certified=False,remote='not_checked',agent_evals='not_run',global_activation=False)))
'''
environment = dict(os.environ)
environment.pop('PYTHONPATH', None)
run = subprocess.run([str(interpreter), '-I', '-c', code, str(scratch)], cwd=scratch,
    env=environment, capture_output=True, encoding='utf-8', timeout=120)
assert run.returncode == 0, (run.stdout,run.stderr)
result = dict(schema_version=1,wheel=wheel.name,wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),
    installed_isolated=True,exit_code=run.returncode,smoke=json.loads(run.stdout))
(root/'docs/evidence/guided-onboarding-wheel-smoke.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('Installed guided onboarding/resources verified; Desktop/remote are not certified')
