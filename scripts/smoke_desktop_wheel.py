"""Installed-package smoke using disposable clients; never run a Codex model."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid

root = Path(__file__).resolve().parents[1]
interpreter = root / '.smoke-venv/Scripts/python.exe'
wheel = root / 'dist/crea_local_harness-0.1.0-py3-none-any.whl'
scratch = root / '.test-data' / ('desktop-wheel-' + uuid.uuid4().hex)
scratch.mkdir(parents=True)
code = '''
import hashlib,json,sys,subprocess,tomllib
from pathlib import Path
from importlib.resources import files
import harness_core,harness_local
from harness_core.desktop import activate_profiles,DesktopCertificate,assess_certificate
from harness_local.desktop_resources import load_desktop,render_integration
from harness_local.desktop_integration import preview,apply,recover
from harness_core.supervised import SupervisedAcceptance,assess_preparation
from harness_local.supervised import capture,compare
assert 'site-packages' in harness_local.__file__ and 'site-packages' in harness_core.__file__
base=Path(sys.argv[1]); target=base/'client'; target.mkdir()
subprocess.run(['git','init','--initial-branch=develop',str(target)],check=True,capture_output=True)
subprocess.run(['git','-C',str(target),'remote','add','origin','https://github.com/demo/alpha.git'],check=True,capture_output=True)
(target/'.harness').mkdir()
(target/'.harness/client.yaml').write_text(json.dumps(dict(schema_version=1,client_id='alpha',repository='demo/alpha',base_branch='develop',openspec_root='openspec')))
policy=base/'policy.json'
policy.write_text(json.dumps(dict(schema_version=1,policy_id='synthetic',client_id='alpha',repository='demo/alpha',base_branch='develop',branch_prefix='codex/',read_only_paths=['.harness/'],denied_paths=['private/'],max_files=40,max_bytes=2000000)))
binding=base/'binding.json'
binding.write_text(json.dumps(dict(schema_version=1,client_id='alpha',checkout_id='wheel',target_path=str(target),policy_sha256=hashlib.sha256(policy.read_bytes()).hexdigest(),state_dir=str(base/'state/alpha/wheel'))))
original=b'# Synthetic custom instructions\\r\\n'
(target/'AGENTS.md').write_bytes(original)
catalog=load_desktop()
assert len(catalog.roles)==8 and all(not r.activated for r in catalog.roles)
selected=activate_profiles(catalog,{'developer':{'model':'synthetic-model','effort':'high'},'auditor':{'model':'synthetic-model','effort':'high'}},{'synthetic-model':['high']})
content=render_integration(selected)
assert tomllib.loads(content['.codex/agents/harness-auditor.toml'])['sandbox_mode']=='read-only'
plan=base/'plan.json'
result,exit=preview(target,policy,binding,selected,plan_out=plan)
assert exit==0 and result['desktop_status']=='not_checked'
result,exit=apply(target,policy,plan)
assert exit==0 and (target/'AGENTS.md').read_bytes().startswith(original)
assert (target/'.agents/skills/harness-hu/SKILL.md').exists()
certificate=DesktopCertificate(schema_version=1,catalog_sha256=selected.sha256,app_version='synthetic-not-observed',engine_version='synthetic-not-observed',account_ref='synthetic',observations=[])
assert assess_certificate(selected,certificate)['certified'] is False
(target/'candidate.txt').write_text('synthetic candidate')
snapshot=capture(target,policy,binding,['candidate.txt'],selected.sha256,certificate)
assert compare(target,policy,binding,snapshot,certificate)['intact']
assert not assess_preparation(selected,certificate,snapshot,None)['prepared']
(target/'candidate.txt').write_text('changed')
assert compare(target,policy,binding,snapshot,certificate)['status']=='blocked'
result,exit=recover(target,policy,plan,apply_changes=True)
assert exit==0 and (target/'AGENTS.md').read_bytes()==original
for name in ('rolecatalog','toolrequirement','roleassignment','desktopintegrationplan','integrationjournal','desktopcertificate','candidatesnapshot','supervisedacceptance'):
 json.loads(files('harness_core').joinpath('schemas/'+name+'.schema.json').read_bytes())
assert not any(m.startswith(('pyspark','mlflow','databricks')) for m in sys.modules)
print(json.dumps(dict(checks=15,roles=8,configured_synthetic_profiles=2,schemas=8,desktop='not_checked',agent_execution='not_run',certified=False,global_activation=False)))
'''
environment = dict(os.environ)
environment.pop('PYTHONPATH', None)
run = subprocess.run([str(interpreter), '-I', '-c', code, str(scratch)], cwd=scratch,
                     env=environment, capture_output=True, encoding='utf-8', timeout=60)
assert run.returncode == 0, (run.stdout, run.stderr)
result = dict(schema_version=1, wheel=wheel.name, wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),
              installed_isolated=True, exit_code=run.returncode, smoke=json.loads(run.stdout))
(root / 'docs/evidence/desktop-wheel-smoke.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print('Installed desktop resources and integration verified; Desktop remains not_checked')
