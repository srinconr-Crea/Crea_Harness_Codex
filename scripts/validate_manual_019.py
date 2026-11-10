"""Validación mantenedor: candidato exacto en fixture local, usando plan/run/gate real.

No configura un proyecto de negocio ni acredita un piloto nativo. La preparación y
el run son operaciones separadas; los recibos primarios se conservan por bytes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'artifacts/crea-manual-kit-0.1.9'
CHANGE='habilitar-trabajo-multidesarrollador-kit'
EVIDENCE=ROOT/'docs/hu'/CHANGE


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(root,*args):
    r=subprocess.run(['git','-c','core.autocrlf=false',*args],cwd=root,capture_output=True,text=True)
    if r.returncode:raise ValueError(r.stderr)
    return r.stdout.strip()


def pointer_for(attempt):
    return EVIDENCE/('fixture-019.json' if attempt==1 else f'fixture-019-attempt-{attempt}.json')


def prepare(attempt):
    pointer=pointer_for(attempt)
    if pointer.exists():raise ValueError('VALIDATION_FIXTURE_ALREADY_PREPARED')
    result=subprocess.run([sys.executable,'-B',str(SOURCE/'scripts/crea/composicion.py'),'--root',str(SOURCE)],capture_output=True,text=True,check=True)
    selection=json.loads(result.stdout)
    names=sorted(selection['client_required']+selection['distribution_only'])
    fixture=ROOT.parent/'.test-data'/('v019-'+uuid.uuid4().hex[:8])
    fixture.mkdir(parents=True)
    hashes={}
    for name in names:
        target=fixture/'candidate'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(SOURCE/name,target);hashes[name]=sha(target)
    git(fixture,'init','-b','codex/validation019');git(fixture,'config','user.name','Local validation fixture')
    git(fixture,'config','user.email','fixture.invalid')
    (fixture/'.gitignore').write_text('.crea/\n.test-work/\n',encoding='utf-8')
    (fixture/'pytest.ini').write_text('[pytest]\n',encoding='utf-8')
    runner='''import os,subprocess,sys
from pathlib import Path
git_directory=Path(sys.argv[1])
if not git_directory.is_absolute() or not (git_directory/'git.exe').is_file():raise ValueError('REVIEWED_GIT_REQUIRED')
os.environ['PATH']=str(git_directory)+os.pathsep+os.environ.get('PATH','')
os.environ['GIT_TERMINAL_PROMPT']='0'
os.environ['GCM_INTERACTIVE']='never'
raise SystemExit(subprocess.call([sys.executable,'-B','-m','pytest','-c','pytest.ini','-q','-p','no:cacheprovider','-p','junit_subcases','candidate/tests/crea','--junitxml='+sys.argv[2]]))
'''
    (fixture/'runner.py').write_text(runner,encoding='utf-8')
    shutil.copyfile(ROOT/'scripts/pytest019_subcases.py',fixture/'junit_subcases.py')
    sys.path.insert(0,str(SOURCE/'scripts/crea'))
    from testing.common import digest
    git_directory=str(Path(shutil.which('git')).parent)
    prefix='docs/hu/'+CHANGE+f'/pruebas/attempt-{attempt}/'
    tests={
        'CA01':['test_team_delivery.TeamDeliveryTests::test_independent_target_and_legacy_fallback'],
        'CA02':['test_local_environment.LocalEnvironmentTests::test_shared_binding_plan_is_rebuilt_and_alias_does_not_change_python_identity'],
        'CA03':['test_developer_preparation.DeveloperPreparationTests::test_bind_preview_and_repeat_are_local_and_idempotent'],
        'CA04':['test_target_compatibility.TargetCompatibilityTests::test_A_independent_stories_continue_with_current_bounded_evidence'],
        'CA05':['test_target_compatibility.TargetCompatibilityTests::test_C_same_rule_incompatible_and_D_clean_git_contradiction',
                'test_target_compatibility.TargetCompatibilityTests::test_C_same_rule_incompatible_and_D_clean_git_contradiction[crea-subcase-1]',
                'test_target_compatibility.TargetCompatibilityTests::test_C_same_rule_incompatible_and_D_clean_git_contradiction[crea-subcase-2]'],
        'CA06':['test_content_v3.ContentV3Tests::test_real_plan_run_gate_remains_current_after_declared_observation'],
        'CA07':['test_client_composition.ClientCompositionTests::test_client_has_local_entry_without_distribution_prompts'],
        'CA08':['test_developer_preparation.DeveloperPreparationTests::test_online_read_distinguishes_denial_connection_and_unverifiable_response'+suffix
                for suffix in ['',*[f'[crea-subcase-{n}]' for n in range(1,6)]]]}
    # Use actual node names; fail preparation if a representative assertion is absent.
    import ast
    available=set()
    for file in (SOURCE/'tests/crea').glob('test_*.py'):
        for node in ast.walk(ast.parse(file.read_text(encoding='utf-8-sig'))):
            if isinstance(node,ast.ClassDef):
                available.update(file.stem+'.'+node.name+'::'+n.name for n in node.body if isinstance(n,ast.FunctionDef))
    if set(x.split('[crea-subcase-')[0] for rows in tests.values() for x in rows)-available:raise ValueError('ASSERTION_NODE_NOT_FOUND')
    tests={key:['candidate.tests.crea.'+node for node in rows] for key,rows in tests.items()}
    outputs=[prefix+n for n in ['plan.json','git.json','resultados.json','gate.json','junit-kit-regression.xml','receipt-kit-regression.json','stdout-kit-regression.log','stderr-kit-regression.log']]
    policy={'schema_version':'1.0','policy_id':'maintainer019','version':'1','setup_complete':True,
        'checks':[{'id':'kit-regression','kind':'pytest','environment':'local','effect':'local_execution',
        'argv':['python','-B','runner.py',git_directory,prefix+'junit-kit-regression.xml'],
        'configured':True,'timeout_seconds':3600,'inputs':['candidate/'+n for n in names]+['runner.py','junit_subcases.py','pytest.ini'],
        'criteria':list(tests),'required_assertions':list(tests),'min_tests':177,'reuse_seconds':0}],
        'rules':[{'id':'LOCAL019','paths':['*'],'checks':['kit-regression'],'reason':'Isolated candidate validation; never publish fixture'}]}
    settings={'schema_version':'1.0','python_executable':None,'local_environment_path':'.crea/local.json',
        'reviewed_policy_digest':digest(policy),'max_evidence_age_seconds':7200,'outputs':outputs,
        'checks':{'kit-regression':{'junit_path':prefix+'junit-kit-regression.xml','assertion_tests':tests,
                  'coverage_path':None,'coverage_files':[],'coverage_minimum':None}}}
    project=read(SOURCE/'docs/proyecto.json');project['project']['setup_complete']=True
    project['validation']['required_checks']=[]
    write(fixture/'docs/proyecto.json',project);write(fixture/'policy.json',policy);write(fixture/'execution.json',settings)
    write(fixture/'.crea/local.json',{'schema_version':'1.0','python_executable':sys.executable})
    git(fixture,'add','--','candidate','runner.py','junit_subcases.py','pytest.ini','.gitignore','docs/proyecto.json','policy.json','execution.json')
    git(fixture,'commit','-m','Exact 019 candidate and reviewed local validation configuration')
    base=git(fixture,'rev-parse','HEAD')
    (fixture/'validation-intent.md').write_text('Execute reviewed candidate internal regressions; no native or real remote pilot.\n',encoding='utf-8')
    from testing import workflow,git_adapter
    from datetime import datetime,timezone
    handoff_name='docs/hu/'+CHANGE+f'/handoffs/planificacion-{attempt}.json'
    entry_name=handoff_name.replace('.json','-entrada.json')
    previous=None
    if attempt>1:
        previous_name='docs/hu/'+CHANGE+f'/handoffs/planificacion-{attempt-1}.json'
        prior=ROOT/previous_name
        if not prior.is_file():raise ValueError('PREVIOUS_VALIDATION_HANDOFF_REQUIRED')
        for old in prior.parent.glob('planificacion-*.json'):
            target=fixture/old.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old,target)
        previous={'path':previous_name,'sha256':sha(prior)}
    write(fixture/entry_name,git_adapter.observe(fixture))
    handoff={'schema_version':'1.0',
        'identity':{'hu_id':CHANGE,'external_story_id':None,'change':CHANGE,'phase':'planificacion','attempt':attempt,
                    'sender':'planner','recipient':'principal','agent_id':None,'created_at':datetime.now(timezone.utc).isoformat()},
        'result':{'status':'ready','completed':['Reconciled validation scope after implementation; no future test results claimed']},
        'scope':{'objective':'Validate exact portable 019 bytes in isolated local fixture; not a native business HU pilot',
            'criteria':[{'path':'validation-intent.md','sha256':sha(fixture/'validation-intent.md')}],
            'approved_paths':['candidate/'+name for name in names],
            'read_paths':['candidate/'+name for name in names]+['policy.json','execution.json','runner.py'],
            'write_paths':outputs+[handoff_name,entry_name],'actions':['run_tests'],'candidate_digest':None,
            'base':base,'head':base,'entry':{'path':entry_name,'sha256':sha(fixture/entry_name)},'exit':None,
            'moves':[],'sync':[],'git_inputs':{'kit-regression':[]}},
        'context':{'layers':[],'capabilities':[],'not_applicable_reason':'Portable harness local fixtures; no business data layer',
            'rules':[],'functional_decisions':[],
            'risk':{'level':'medium','reason':'Git observations, opt-in projection and environment contracts require regressions'}},
        'evidence':{'artifacts':[],'decisions':[],'objects':[],'validation_plan':{'path':'policy.json','sha256':sha(fixture/'policy.json')},'tests':None,'delivery':None},
        'pending':{'blockers':[],'warnings':[],'questions':[],'exceptions':[]},
        'continuation':{'transition':'to_test','next_step':'Tester execute reviewed local selection once','authorization':None,'decision_required':None},'previous_handoff':previous}
    from testing import schemas
    schemas.validate_schema(read(SOURCE/'docs/plantillas/handoff.schema.json'),handoff)
    write(fixture/handoff_name,handoff)
    plan=workflow.make_plan(fixture,fixture/'policy.json',fixture/'execution.json',base,list(tests))
    if plan['status']!='ready':raise ValueError(str(plan['blockers']))
    write(fixture/outputs[0],plan);write(fixture/outputs[1],git_adapter.collect(fixture,base,outputs))
    write(pointer,{'fixture':str(fixture),'base_sha':base,'source_files':hashes,'outputs':outputs,'plan_id':plan['plan_id'],
                   'limits':['Synthetic local validation checkout; no native roles, real services or two-person pilot']})
    for name in ['policy.json','execution.json',outputs[0],outputs[1],handoff_name,entry_name]:
        target=EVIDENCE/'validation-configuration'/f'attempt-{attempt}'/Path(name).name if '/' not in name else ROOT/name
        if target.exists():raise ValueError('PRIMARY_VALIDATION_OUTPUT_ALREADY_EXISTS')
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(fixture/name,target)
    print(json.dumps({'status':'ready_for_test','fixture':str(fixture),'plan_id':plan['plan_id'],'files':len(hashes)}))


def run(attempt):
    data=read(pointer_for(attempt));fixture=Path(data['fixture']).resolve()
    if fixture.parent!=ROOT.parent/'.test-data' or not fixture.name.startswith('v019-'):raise ValueError('UNEXPECTED_VALIDATION_FIXTURE')
    if any(sha(SOURCE/name)!=value or sha(fixture/'candidate'/name)!=value for name,value in data['source_files'].items()):raise ValueError('CANDIDATE_CHANGED')
    sys.path.insert(0,str(fixture/'candidate/scripts/crea'))
    from testing import workflow
    outputs=data['outputs'];plan=read(fixture/outputs[0])
    result=workflow.run(fixture,fixture/'policy.json',fixture/'execution.json',plan)
    gate=workflow.gate(fixture,fixture/'policy.json',fixture/'execution.json',plan,result)
    write(fixture/outputs[2],result);write(fixture/outputs[3],gate)
    for name in outputs:
        if (fixture/name).is_file():
            target=ROOT/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(fixture/name,target)
    print(json.dumps({'status':gate['status'],'gate':gate,'results':result},ensure_ascii=False))
    return 0 if gate['status']=='passed' else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare','run']);parser.add_argument('--attempt',type=int,default=1)
    args=parser.parse_args()
    if args.attempt<1:raise ValueError('POSITIVE_ATTEMPT_REQUIRED')
    raise SystemExit(prepare(args.attempt) if args.action=='prepare' else run(args.attempt))
