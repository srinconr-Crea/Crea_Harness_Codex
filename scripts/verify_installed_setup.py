"""Real local wheel protocol; synthetic client and no Desktop/remote acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from harness_core.onboarding_plan import canonical
from harness_local import environment_setup as setup
from harness_local.distribution import candidate_manifest

parser=argparse.ArgumentParser()
parser.add_argument('--installation-record',required=True)
parser.add_argument('--scratch',required=True)
args=parser.parse_args()
workspace=Path(__file__).resolve().parents[1]
installation=Path(args.installation_record).resolve()
scratch=Path(args.scratch).resolve()
if scratch.exists(): raise SystemExit('scratch must be a new, explicitly selected directory')
scratch.mkdir()
record=json.loads(installation.read_bytes()); root=Path(record['installation_root'])
assert Path(setup.__file__).is_relative_to(root),setup.__file__
candidate=candidate_manifest(); assert candidate.certified is False and candidate.release_allowed is False
git=next(t['path'] for t in record['tools'] if t['name']=='git')
target=scratch/'client'; target.mkdir()
def git_run(*args):
    subprocess.run([git,'-C',str(target),*args],capture_output=True,check=True)
subprocess.run([git,'init','--initial-branch=main',str(target)],capture_output=True,check=True)
data=json.loads((workspace/'docs/examples/setup/complete.json').read_bytes())
git_run('remote','add','origin',data['repository_url'])
git_run('config','user.name','Synthetic Operator'); git_run('config','user.email','synthetic@example.invalid')
(target/'.harness').mkdir(); (target/'.harness/client.yaml').write_bytes(canonical(data['descriptor']))
git_run('add','.harness/client.yaml'); git_run('commit','-m','Synthetic baseline')
policy=scratch/'policy.json'; policy.write_bytes(canonical(data['policy']))
binding=scratch/'binding.json'
data['binding'].update(target_path=str(target),state_dir=str(scratch/'state/demo/checkout'),
    policy_sha256=hashlib.sha256(policy.read_bytes()).hexdigest())
binding.write_bytes(canonical(data['binding']))
data['access_scope']['policy_sha256']=data['binding']['policy_sha256']
data['guided_request'].update(target_path=str(target),policy_path=str(policy),binding_path=str(binding))
data.update(installation_record=str(installation),installation_kit=record['kit_path'],
    capabilities=['local','git','openspec','desktop','databricks'],commit_local=True)
parent=scratch/'parent.json'
preview,code=setup.preview(data,plan_out=parent); assert code==0,preview
output,code=setup.apply(parent,preview['plan']['plan_sha256']); assert code==0,output
assert output['report']['prepared'] and 'local_clean' in output['report']['hu_admissible']
assert setup.status(parent)[0]['report']['prepared']
assert setup.apply(parent,preview['plan']['plan_sha256'])[0]['idempotent']
assert output['report']['certified'] is False and output['report']['publication_allowed'] is False
assert next(c['reason'] for c in output['report']['capabilities'] if c['id']=='desktop')=='skill_discovery_pending'
assert next(c['reason'] for c in output['report']['capabilities'] if c['id']=='databricks')=='remote_not_checked'
print(json.dumps({'status':'passed','package_path':setup.__file__,'tools':{t['name']:t['version'] for t in record['tools']},
    'candidate_sha256':candidate.manifest_sha256,'report':output['report']},ensure_ascii=False))
