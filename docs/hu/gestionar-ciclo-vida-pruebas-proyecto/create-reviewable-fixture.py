"""Fixture sintético final con evidencia primaria de un único plan, sin remoto."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import uuid
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
KIT=ROOT/'artifacts/crea-manual-kit-0.1.8'
sys.path.insert(0,str(KIT/'tests/crea'))
from test_testing_lifecycle import LifecycleTests
from testing import workflow
from testing.common import write,read

case=LifecycleTests(methodName='test_attempts_two_hu_unchanged_configuration_real_run_gate')
case.setUp()
base,policy,execution=case.fixture()
project=read(KIT/'docs/proyecto.json')
project['project']['setup_complete']=True
project['project']['name']='Fixture sintético de revisión'
project.pop('context_management',None)
project['validation']['testing']['policy_path']='policy.json'
project['validation']['testing']['execution_path']='execution.json'
write(case.root/'docs/proyecto.json',project)
plan=case.plan(base,policy,execution,'reviewer','1')
prefix='docs/hu/reviewer/pruebas/attempt-1/'
write(case.root/(prefix+'plan.json'),plan)
results=workflow.run(case.root,policy,execution,plan)
write(case.root/(prefix+'resultados.json'),results)
with patch.object(workflow.execution,'run_process',side_effect=AssertionError('gate must not execute suites')) as calls:
    verdict=workflow.gate(case.root,policy,execution,plan,results)
write(case.root/(prefix+'gate.json'),verdict)
assert verdict['status']=='passed',verdict
target=Path(__file__).parent/'fixtures'/('reviewable-'+uuid.uuid4().hex[:8])
shutil.copytree(case.root,target)
with patch.object(workflow.execution,'run_process',side_effect=AssertionError('copied gate must not execute suites')) as copied_calls:
    copied=workflow.gate(target,target/'policy.json',target/'execution.json',read(target/(prefix+'plan.json')),read(target/(prefix+'resultados.json')))
assert copied['status']=='passed',copied
cli=subprocess.run([sys.executable,'-B',str(KIT/'scripts/crea/pruebas.py'),'gate','--repo',str(target),
                   '--policy','policy.json','--execution','execution.json','--plan',prefix+'plan.json'],capture_output=True,text=True)
assert cli.returncode==0,(cli.stdout,cli.stderr)
receipt={'fixture':str(target),'plan':prefix+'plan.json','results':prefix+'resultados.json','gate':prefix+'gate.json',
         'plan_id':plan['plan_id'],'status':copied['status'],'suite_calls_from_gate':len(calls.call_args_list)+len(copied_calls.call_args_list),
         'cli_gate_exit':cli.returncode,'cli_gate':json.loads(cli.stdout)}
write(Path(__file__).parent/'reviewable-fixture.json',receipt)
print(json.dumps(receipt))
case.doCleanups()
