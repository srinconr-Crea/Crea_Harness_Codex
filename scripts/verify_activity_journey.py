"""Run the installed-package journey on selected local/synthetic client inputs.

No remote writes, fabricated reviews or internal Desktop data. Invoke with -I -B
from an installed runtime. A new scratch and an explicitly selected checkout are
required; all client state is external. The selected branch must be disposable.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from harness_core.configuration import normalize_remote
from harness_core.contracts import Binding
from harness_core.desktop import activate_profiles
from harness_core.onboarding_plan import canonical, sha, separate
from harness_local import environment_setup as setup
from harness_local.activity_execution import run as execute
from harness_local.activity_ledger import ActivityLedger
from harness_local.desktop_resources import load_desktop
from harness_local.work import WorkService


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--target',required=True)
    parser.add_argument('--scratch',required=True)
    parser.add_argument('--client-id',required=True)
    parser.add_argument('--base-branch',required=True)
    parser.add_argument('--model',required=True)
    parser.add_argument('--effort',default='medium')
    parser.add_argument('--installation-record')
    args=parser.parse_args()
    target=Path(args.target).resolve(); scratch=Path(args.scratch).resolve()
    separate([str(target),str(scratch)])
    if scratch.exists(): raise SystemExit('scratch must be absent')
    def git(*values):
        return subprocess.check_output(['git','-C',str(target),*values],stderr=subprocess.PIPE).decode().strip()
    if git('status','--porcelain'): raise SystemExit('selected checkout must be clean')
    # Never choose a user identity, remote, branch or checkout implicitly.
    if not git('config','user.name') or not git('config','user.email'): raise SystemExit('local Git identity required')
    branch=git('branch','--show-current')
    if not branch.startswith('codex/'): raise SystemExit('select a codex/ pilot branch first')
    repository=normalize_remote(git('remote','get-url','origin'))
    tracked=git('ls-files').splitlines()
    scratch.mkdir(parents=True)
    client=args.client_id; checkout='pilot'
    descriptor=dict(schema_version=1,client_id=client,repository=repository,base_branch=args.base_branch,openspec_root='openspec')
    (target/'.harness').mkdir(exist_ok=True)
    descriptor_path=target/'.harness/client.yaml'
    if descriptor_path.exists(): raise SystemExit('fresh selected checkout required')
    descriptor_path.write_bytes(canonical(descriptor))
    git('add','--','.harness/client.yaml')
    git('commit','-m','Preparar descriptor del piloto local seleccionado')
    policy=dict(schema_version=1,policy_id='local-pilot',client_id=client,repository=repository,
        base_branch=args.base_branch,branch_prefix='codex/',read_only_paths=[],denied_paths=['private/'],max_files=64,max_bytes=2000000)
    policy_path=scratch/'policy.json'; policy_path.write_bytes(canonical(policy))
    binding=dict(schema_version=1,client_id=client,checkout_id=checkout,target_path=str(target),
        policy_sha256=sha(policy_path.read_bytes()),state_dir=str(scratch/'state'/client/checkout))
    binding_path=scratch/'binding.json'; binding_path.write_bytes(canonical(binding))
    profiles={role.id:dict(model=args.model,effort=args.effort) for role in load_desktop().roles}
    catalog=activate_profiles(load_desktop(),profiles,{args.model:[args.effort]})
    development=dict(schema_version=1,client_id=client,stack=['Python'],conventions=['unittest'],
        business_rules=['Solo cantidades sintéticas; suma decimal local; sin recursos remotos'],roles=list(profiles),
        validations=['unittest'],sources={k:'user' for k in ('stack','conventions','business_rules','roles','validations')})
    request=dict(schema_version=1,target_path=str(target),policy_path=str(policy_path),binding_path=str(binding_path),
        repository=repository,base_branch=args.base_branch,development=development,catalog=catalog.model_dump(),
        tool_binding=dict(schema_version=1,client_id=client,checkout_id=checkout,tools=[]))
    data=dict(schema_version=1,descriptor=descriptor,policy=policy,binding=binding,
        access_scope=dict(schema_version=1,client_id=client,policy_sha256=binding['policy_sha256'],
            read_allow=[*tracked,'harness_pilot/'],write_allow=['harness_pilot/'],deny=['private/']),
        capabilities=['local','git','desktop'],sources={k:'user' for k in ('descriptor','policy','binding','access_scope','capabilities')},
        guided_request=request,commit_local=True)
    if args.installation_record:
        installation_path=Path(args.installation_record).resolve()
        installation=json.loads(installation_path.read_bytes())
        assert Path(setup.__file__).is_relative_to(Path(installation['installation_root']))
        data.update(installation_record=str(installation_path),installation_kit=installation['kit_path'])
        if any(tool['name']=='openspec' for tool in installation['tools']): data['capabilities'].append('openspec')
    before={str(p):sha(p.read_bytes()) for p in target.rglob('*') if p.is_file()}
    (scratch/'setup-input.json').write_bytes(canonical(data))
    preview,code=setup.preview(data)
    (scratch/'setup-preview.json').write_bytes(canonical(preview))
    assert code==0,dict(blockers=preview.get('plan',{}).get('blockers'),
        children={name:json.loads(content).get('blockers') for name,content in preview.get('plan',{}).get('child_payloads',{}).items()})
    assert before=={str(p):sha(p.read_bytes()) for p in target.rglob('*') if p.is_file()}
    assert not Path(binding['state_dir']).exists()
    parent=scratch/'setup-plan.json'; parent.write_bytes(canonical(preview['plan']))
    prepared,code=setup.apply(parent,preview['plan']['plan_sha256'])
    assert code==0 and prepared['report']['prepared'],prepared
    assert not prepared['report']['certified'] and not prepared['report']['publication_allowed']
    return journey(args,target,scratch,policy_path,binding_path,binding,branch)


def journey(args,target,scratch,policy_path,binding_path,binding,branch):
    client=args.client_id
    selected=Binding.model_validate(binding); ledger=ActivityLedger(selected)
    assert ledger.path.is_file() and not (ledger.state/'hu.sqlite3').exists()
    work=WorkService(target,policy_path,binding_path)
    raw=dict(schema_version=1,story_id='LOCAL-PILOT',story='Sumar cantidades sintéticas con precisión decimal',writer_actor='principal',
        criteria=['Vacío devuelve cero; 0.1 + 0.2 devuelve 0.3; -1 + 2 devuelve 1'],
        paths=['harness_pilot/total.py','harness_pilot/test_total.py'],operations=['create'],tests=['pilot-unit'],
        mode='supervised_single_agent',available_models={args.model:[args.effort]})
    ledger_before=ledger.path.read_bytes()
    planned=work.preview(raw); assert planned['status']=='ready',planned
    assert ledger.path.read_bytes()==ledger_before and not (ledger.state/'hu.sqlite3').exists()
    started=work.start(raw,planned['plan']['plan_sha256']); assert started['run']['state']=='approved',started
    assert work.start(raw,planned['plan']['plan_sha256'])['idempotent']
    work.hu.run('transition','LOCAL-PILOT','implement',dict(schema_version=1,state='implementing'))
    folder=target/'harness_pilot'; folder.mkdir()
    (folder/'total.py').write_text('from decimal import Decimal\ndef total(values):\n    return sum((Decimal(str(v)) for v in values), Decimal("0"))\n',encoding='utf-8')
    (folder/'test_total.py').write_text('''import importlib.util
from pathlib import Path
from decimal import Decimal
import unittest
spec=importlib.util.spec_from_file_location('pilot_total',Path(__file__).with_name('total.py'))
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
class Totals(unittest.TestCase):
    def test_empty(self): self.assertEqual(module.total([]),Decimal('0'))
    def test_decimal(self): self.assertEqual(module.total([0.1,0.2]),Decimal('0.3'))
    def test_signed(self): self.assertEqual(module.total([-1,2]),Decimal('1'))
''',encoding='utf-8')
    candidate=work.hu.run('candidate','LOCAL-PILOT','candidate',{'schema_version':1})
    assert candidate['status']=='ready',candidate
    candidate_hash=candidate['run']['candidate']['candidate_sha256']
    assert work.hu.run('transition','LOCAL-PILOT','validating',dict(schema_version=1,state='validating'))['status']=='ready'
    context=dict(schema_version=1,target_path=str(target),policy_path=str(policy_path),binding_path=str(binding_path),
        hu_id='LOCAL-PILOT',attempt=1,operation_id='pilot-unit')
    def tests():
        check=subprocess.run([sys.executable,'-I','-B','-m','unittest','discover','-s',str(folder)],capture_output=True)
        return dict(status='passed' if check.returncode==0 else 'failed',returncode=check.returncode)
    tested=execute(context,'pilot_unit',tests); assert tested['status']=='passed',tested
    work.hu.run('evidence','LOCAL-PILOT','unit-evidence',dict(schema_version=1,id='pilot-unit',candidate_sha256=candidate_hash,
        status='passed',simulated=False,actor='principal',kind='test',evidence_ref='local-unittest-three-cases'))
    # Abrupt process exit after durable own start, before any result.
    interrupted=subprocess.run([sys.executable,'-I','-B','-c',
        'import json,os,sys; from harness_core.contracts import Binding; from harness_local.activity_ledger import ActivityLedger; '
        'b=Binding.model_validate(json.load(open(sys.argv[1]))); '
        'l=ActivityLedger(b); c=l.operation("process-interruption",scope="hu",hu_id="LOCAL-PILOT",attempt=1); c.__enter__(); os._exit(17)',str(binding_path)],capture_output=True)
    assert interrupted.returncode==17
    assert ledger.report()['incomplete_operations']==1
    # A new process reads persisted HU; it never fabricates a result for the killed command.
    resumed=subprocess.run([sys.executable,'-I','-B','-m','harness_local','work','resume','--path',str(target),
        '--policy',str(policy_path),'--binding',str(binding_path),'--story','LOCAL-PILOT','--operation','fresh-process-resume','--json'],capture_output=True)
    assert resumed.returncode==0,resumed.stdout.decode(errors='replace')
    report_before=ledger.path.read_bytes()
    report=ledger.report(dict(schema_version=1,hu_id='LOCAL-PILOT'))
    assert ledger.path.read_bytes()==report_before
    out=scratch/'activity-report.json'; ledger.export(out,dict(schema_version=1,hu_id='LOCAL-PILOT'))
    assert report['input_tokens'] is None and report['cost_usd'] is None
    assert report['incomplete_operations']==1
    final=work.status('LOCAL-PILOT')
    assert final['approval_current'] and final['local_state']=='validating'
    result=dict(status='passed',package_path=__import__('harness_local').__file__,client_id=client,branch=branch,
        setup_prepared=True,tests_passed=3,new_process_resume=True,another_chat='not_run',another_machine='not_run',
        review='blocked_independence_not_observed',remote='not_checked',certified=False,release_allowed=False,
        publication_allowed=False,candidate_sha256=candidate_hash,counts=report['counts'],duration_ms=report['duration_ms'],
        pending_interrupted_operations=report['incomplete_operations'],input_tokens=None,cost_usd=None,
        unavailable_reason=report['unavailable_reason'],state_dir=str(ledger.state),export=str(out))
    (scratch/'journey-result.json').write_bytes(canonical(result))
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__': main()
