"""Exercise installed HU contracts/resources and synthetic local lifecycle."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid

root=Path(__file__).resolve().parents[1]
interpreter=root/'.smoke-venv/Scripts/python.exe'
wheel=root/'dist/crea_local_harness-0.1.0-py3-none-any.whl'
scratch=root/'.test-data'/('hu-wheel-'+uuid.uuid4().hex)
scratch.mkdir(parents=True)
code='''
import json,sys,subprocess
from pathlib import Path
from importlib.resources import files
from harness_core.guided import QuestionnaireDraft
from harness_core.hu import HuRun,PlanRevision,ApprovalRecord,Candidate,Assignment,GateResult
from harness_local.guided_resources import resources
from harness_local.desktop_resources import resources as desktop_resources
from harness_local.guided_onboarding import preview,apply
from harness_local.hu import HuService
from harness_local.diagnostics import Check
base=Path(sys.argv[1]); target=base/'client'; target.mkdir()
def git(*args): return subprocess.run(['git','-C',str(target),*args],check=True,capture_output=True).stdout
git('init','--initial-branch=develop'); git('remote','add','origin','https://github.com/demo/alpha.git')
git('config','core.autocrlf','false')
policy=base/'policy.json'
policy.write_text(json.dumps(dict(schema_version=1,policy_id='synthetic',client_id='alpha',repository='demo/alpha',base_branch='develop',branch_prefix='codex/',read_only_paths=[],denied_paths=['private/'],max_files=64,max_bytes=2000000)))
template=json.loads(resources()['complete-template.json'])
for key,value in dict(target_path=str(target),policy_path=str(policy),binding_path=str(base/'binding.json'),state_dir=str(base/'state/alpha/checkout')).items(): template['answers'][key]['value']=value
draft=QuestionnaireDraft.model_validate(template)
def ready(name): return Check(name,'ready','synthetic','local synthetic probe')
plan=base/'onboarding.json'; preview(draft,probe_fn=ready,plan_out=plan)
prepared,exit_code=apply(plan,stage='prepare',probe_fn=ready)
assert exit_code==0 and prepared['prepared'] and not prepared['certified']
git('add','.'); git('-c','user.name=Smoke','-c','user.email=smoke@example.invalid','commit','-m','prepared')
s=HuService(target,policy,base/'binding.json')
s.run('start','HU1','s',dict(schema_version=1,writer_actor='writer',onboarding_plan=str(plan),simulation=True))
p=s.run('plan','HU1','p',dict(schema_version=1,criteria=['Synthetic sum'],paths=['total.py'],operations=['create','modify'],tests=['T16'],sources={'story':'user'},decisions=['Small HU without mandatory fanout']))['run']['plan']
s.run('approve','HU1','a',dict(schema_version=1,actor='operator',confirmed=True,client_id='alpha',checkout_id='checkout',attempt=1,revision=1,plan_sha256=p['plan_sha256']))
(target/'total.py').write_text('def total(xs): return sum(xs)\\n')
c=s.run('candidate','HU1','c',dict(schema_version=1))['run']['candidate']
s.run('transition','HU1','v',dict(schema_version=1,state='validating'))
s.run('evidence','HU1','t',dict(schema_version=1,id='T16',candidate_sha256=c['candidate_sha256'],status='passed',simulated=True,actor='tester',kind='test',evidence_ref='synthetic-test'))
s.run('transition','HU1','r',dict(schema_version=1,state='reviewing'))
s.run('evidence','HU1','audit',dict(schema_version=1,id='audit',candidate_sha256=c['candidate_sha256'],status='passed',simulated=True,actor='reviewer',kind='review',evidence_ref='synthetic-review'))
result=s.run('transition','HU1','ready',dict(schema_version=1,state='ready_to_publish'))
assert result['status']=='partial' and result['run']['state']=='ready_to_publish'
assert not result['publication_allowed'] and not result['certified']
assert s.run('transition','HU1','publish',dict(schema_version=1,state='published'))['status']=='blocked'
before=len(s.run('status','HU1')['history'])
assert s.run('transition','HU1','publish',dict(schema_version=1,state='published'))['idempotent']
assert len(s.run('status','HU1')['history'])==before
(target/'total.py').write_text('changed\\n')
assert s.run('resume','HU1','resume',dict(schema_version=1))['status']=='blocked'
artifact=json.loads((s.state/'hu-artifacts/HU1.json').read_text())
assert artifact['run']['candidate'] is None
for model in (HuRun,PlanRevision,ApprovalRecord,Candidate,Assignment,GateResult):
    json.loads(files('harness_core').joinpath('schemas/'+model.__name__.lower()+'.schema.json').read_bytes())
assert desktop_resources()['harness-hu/SKILL.md']
assert not any(m.startswith(('pyspark','mlflow','databricks')) for m in sys.modules)
print(json.dumps(dict(client='synthetic',ready_to_publish='partial',simulated_evidence=True,publication_allowed=False,certified=False,schemas=6,stale_candidate='blocked',idempotent=True,agent_evals='not_run',global_activation=False)))
'''
environment=dict(os.environ); environment.pop('PYTHONPATH',None)
run=subprocess.run([str(interpreter),'-I','-c',code,str(scratch)],cwd=scratch,env=environment,
    capture_output=True,encoding='utf-8',timeout=180)
assert run.returncode==0,(run.stdout,run.stderr)
result=dict(schema_version=1,wheel=wheel.name,wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),
    installed_isolated=True,exit_code=run.returncode,smoke=json.loads(run.stdout))
(root/'docs/evidence/hu-lifecycle-wheel-smoke.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('Installed HU lifecycle/schemas/resources verified with explicitly simulated evidence')
