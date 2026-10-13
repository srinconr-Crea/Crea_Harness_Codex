import argparse
import json
import sys

from harness_core.configuration import ConfigError
from . import __version__
from .diagnostics import Check, doctor
from .onboarding import preview
from .application import apply, recover


class Parser(argparse.ArgumentParser):
    def error(self,message):
        raise ConfigError('invalid_arguments')


def main(argv=None):
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    argv=list(sys.argv[1:] if argv is None else argv)
    parser=Parser(prog='harness',description='Diagnóstico, preparación local explícita y recuperación.')
    parser.add_argument('--version',action='version',version=__version__)
    commands=parser.add_subparsers(dest='command',required=True)
    hu=commands.add_parser('hu')
    hu.add_argument('action',choices=('start','plan','approve','candidate','status','transition','evidence',
        'assign','correct','block','resume','handoff','worktree','attempt'))
    for field in ('path','policy','binding','story'):
        hu.add_argument('--'+field,required=True)
    hu.add_argument('--operation')
    hu.add_argument('--input')
    hu.add_argument('--json',action='store_true')
    onboard=commands.add_parser('onboard')
    for field in ('config','plan','plan-out','evidence'):
        onboard.add_argument('--'+field)
    onboard.add_argument('--stage',choices=('prepare','integrate','certify'))
    onboard.add_argument('--json',action='store_true')
    onboard.add_argument('--recover-apply',action='store_true')
    onboard_modes=onboard.add_mutually_exclusive_group(required=True)
    onboard_modes.add_argument('--dry-run',action='store_true')
    onboard_modes.add_argument('--apply',action='store_true')
    onboard_modes.add_argument('--recover',action='store_true')
    integration=commands.add_parser('integrate')
    integration.add_argument('--path')
    integration.add_argument('--policy')
    integration.add_argument('--binding')
    integration.add_argument('--catalog')
    integration.add_argument('--plan')
    integration.add_argument('--plan-out')
    integration.add_argument('--json',action='store_true')
    integration_modes=integration.add_mutually_exclusive_group(required=True)
    integration_modes.add_argument('--dry-run',action='store_true')
    integration_modes.add_argument('--apply',action='store_true')
    integration_modes.add_argument('--recover',action='store_true')
    integration.add_argument('--recover-apply',action='store_true')
    certificate=commands.add_parser('desktop-check')
    certificate.add_argument('--catalog')
    certificate.add_argument('--observations')
    certificate.add_argument('--json',action='store_true')
    for name in ('review-snapshot','review-compare','supervised-prepare'):
        p=commands.add_parser(name)
        for field in ('path','policy','binding','catalog','observations'):
            p.add_argument('--'+field,required=True)
        p.add_argument('--json',action='store_true')
        if name=='review-snapshot':
            p.add_argument('--scope',action='append',required=True)
            p.add_argument('--out')
        else:
            p.add_argument('--snapshot',required=True)
        if name=='supervised-prepare':
            p.add_argument('--plan',required=True)
            p.add_argument('--acceptance')
            p.add_argument('--require',action='append',default=[])
    for name in ('doctor','init','recover'):
        p=commands.add_parser(name)
        p.add_argument('--path')
        p.add_argument('--policy')
        p.add_argument('--binding')
        p.add_argument('--json',action='store_true')
        if name in ('init','recover'):
            modes=p.add_mutually_exclusive_group()
            modes.add_argument('--dry-run',action='store_true')
            modes.add_argument('--apply',action='store_true')
            p.add_argument('--plan')
        if name=='init':
            p.add_argument('--repo')
            p.add_argument('--base-branch')
            p.add_argument('--binding-out')
            p.add_argument('--checkout-id')
            p.add_argument('--state-dir')
            p.add_argument('--databricks-profile')
            p.add_argument('--plan-out')
        if name=='recover':
            p.add_argument('--run')
    command=next((c for c in ('hu','onboard','init','recover','doctor','integrate','desktop-check','review-snapshot','review-compare','supervised-prepare') if c in argv),'doctor')
    json_mode='--json' in argv
    try:
        args=parser.parse_args(argv)
        if args.command=='hu':
            from .hu import HuService
            from harness_core.configuration import load_document
            if args.action=='status':
                if args.input or args.operation: raise ConfigError('invalid_arguments')
                payload=None
            else:
                if not args.input or not args.operation: raise ConfigError('invalid_arguments')
                payload=load_document(args.input)
            result=HuService(args.path,args.policy,args.binding).run(args.action,args.story,args.operation,payload)
            code=1 if result['status']=='blocked' else 0
        elif args.command=='onboard':
            from . import guided_onboarding as guided
            from harness_core.guided import QuestionnaireDraft,CertificationInput,sanitize
            from harness_core.configuration import load_document
            if args.dry_run:
                if not args.config or any((args.plan,args.stage,args.evidence,args.recover_apply)):
                    raise ConfigError('invalid_arguments')
                raw=load_document(args.config); sanitize(raw)
                draft=guided.parse(QuestionnaireDraft,raw)
                result,code=guided.preview(draft,plan_out=args.plan_out)
            elif args.apply:
                if not args.plan or not args.stage or any((args.config,args.plan_out,args.recover_apply)):
                    raise ConfigError('invalid_arguments')
                if (args.stage=='certify') != bool(args.evidence): raise ConfigError('invalid_arguments')
                evidence=guided.parse(CertificationInput,load_document(args.evidence)) if args.evidence else None
                result,code=guided.apply(args.plan,stage=args.stage,evidence=evidence)
            else:
                if not args.plan or args.stage not in ('prepare','integrate') or any((args.config,args.plan_out,args.evidence)):
                    raise ConfigError('invalid_arguments')
                result,code=guided.recover(args.plan,stage=args.stage,apply_changes=args.recover_apply)
        elif args.command in ('review-snapshot','review-compare','supervised-prepare'):
            from . import supervised
            from harness_core.desktop import RoleCatalog,DesktopCertificate
            from harness_core.supervised import CandidateSnapshot,SupervisedAcceptance
            from harness_core.onboarding_plan import load_json,canonical,separate
            from harness_core.configuration import safe_path,reject_secrets
            from .windows_fs import PinnedTree
            catalog=load_json(args.catalog,RoleCatalog)
            observations=load_json(args.observations,DesktopCertificate)
            if args.command=='review-snapshot':
                snapshot=supervised.capture(args.path,args.policy,args.binding,args.scope,catalog.sha256,observations)
                if args.out:
                    out=safe_path(args.out)
                    separate([str(out),str(safe_path(args.path)),str(safe_path(args.policy)),str(safe_path(args.binding)),
                              str(safe_path(args.catalog)),str(safe_path(args.observations))])
                    _,config=supervised.selected(args.path,args.policy,args.binding)
                    separate([str(out),config['binding'].state_dir])
                    reject_secrets(snapshot.model_dump())
                    with PinnedTree(out.parent) as tree:
                        with tree.file(out.name,create=True) as handle:
                            handle.write(canonical(snapshot.model_dump())+b'\n')
                result=dict(schema_version=1,command=args.command,status='ready',checks=[],
                    snapshot=snapshot.model_dump(),candidate_sha256=snapshot.sha256,certified=False)
            else:
                snapshot=load_json(args.snapshot,CandidateSnapshot)
                if catalog.sha256!=snapshot.catalog_sha256:
                    raise ConfigError('supervised_identity_mismatch')
                if args.command=='review-compare':
                    result=supervised.compare(args.path,args.policy,args.binding,snapshot,observations)
                else:
                    acceptance=load_json(args.acceptance,SupervisedAcceptance) if args.acceptance else None
                    result=supervised.prepare(args.path,args.policy,args.binding,args.plan,catalog,observations,snapshot,acceptance,required=args.require)
            code=1 if result['status']=='blocked' else 0
        elif args.command=='integrate':
            from . import desktop_integration
            from harness_core.desktop import RoleCatalog
            from harness_core.onboarding_plan import load_json
            if not args.path or not args.policy:
                raise ConfigError('configuration_inputs_required')
            if args.dry_run:
                if not args.catalog or not args.binding or args.plan or args.recover_apply:
                    raise ConfigError('invalid_arguments')
                catalog=load_json(args.catalog,RoleCatalog)
                result,code=desktop_integration.preview(args.path,args.policy,args.binding,catalog,plan_out=args.plan_out)
            elif args.apply:
                if not args.plan or any((args.catalog,args.binding,args.plan_out,args.recover_apply)):
                    raise ConfigError('invalid_arguments')
                result,code=desktop_integration.apply(args.path,args.policy,args.plan)
            else:
                if not args.plan or any((args.catalog,args.binding,args.plan_out)):
                    raise ConfigError('invalid_arguments')
                result,code=desktop_integration.recover(args.path,args.policy,args.plan,apply_changes=args.recover_apply)
        elif args.command=='desktop-check':
            from harness_core.desktop import RoleCatalog,DesktopCertificate,assess_certificate
            from harness_core.onboarding_plan import load_json
            if not args.catalog or not args.observations:
                raise ConfigError('configuration_inputs_required')
            result=assess_certificate(load_json(args.catalog,RoleCatalog),load_json(args.observations,DesktopCertificate))
            code=1 if result['status']=='blocked' else 0
        elif args.command=='init':
            if not args.dry_run and not args.apply:
                raise ConfigError('apply_not_supported')
            if not args.path or not args.policy:
                raise ConfigError('configuration_inputs_required')
            if args.apply:
                if not args.plan or any(x is not None for x in (args.binding,args.binding_out,args.checkout_id,
                        args.state_dir,args.databricks_profile,args.plan_out,args.repo,args.base_branch)):
                    raise ConfigError('invalid_arguments')
                result,code=apply(args.path,args.policy,args.plan)
            else:
                if args.plan:
                    raise ConfigError('invalid_arguments')
                result,code=preview(args.path,args.policy,args.binding,args.repo,args.base_branch,
                    binding_out=args.binding_out,checkout_id=args.checkout_id,state_dir=args.state_dir,
                    databricks_profile=args.databricks_profile,plan_out=args.plan_out)
        elif args.command=='recover':
            if not args.path or not args.policy or not args.run or not (args.dry_run or args.apply):
                raise ConfigError('configuration_inputs_required')
            result,code=recover(args.path,args.policy,args.run,binding_path=args.binding,
                                plan_path=args.plan,apply_changes=args.apply)
        else:
            result,code=doctor(args.path,args.policy,args.binding)
    except (ConfigError, OSError, UnicodeError) as error:
        error_code=error.code if isinstance(error,ConfigError) else 'local_read_error'
        result=dict(schema_version=1,command=command,status='invalid',checks=[vars(Check('input','error',error_code,'Entrada o configuración inválida.'))])
        if isinstance(error,ConfigError) and error.document:
            result['checks'][0].update(document=error.document,fields=error.fields)
        conflicts={'stale_plan','plan_identity_mismatch','plan_not_applicable','onboarding_locked','lock_owner_unknown',
                   'recovery_required','application_conflict','confinement_rejected','destination_exists',
                   'write_failed','flush_failed','delete_failed','lock_changed',
                   'integration_drift','integration_identity_mismatch','integration_conflict','integration_policy_blocked',
                   'model_unavailable','effort_unavailable','integration_failed','integration_not_applied',
                   'supervised_identity_mismatch','supervised_evidence_mismatch','candidate_changed_during_capture',
                   'candidate_scope_denied','candidate_too_large'}
        conflicts.update({'guided_prepare_required','guided_role_mismatch','guided_dependency_pending','guided_resource_drift',
                          'guided_recover_integration_first','guided_new_preview_required'})
        conflicts.update({'hu_not_found','hu_identity_mismatch','hu_preparation_required','hu_state_conflict',
            'hu_state_version','hu_operation_conflict','hu_story_exists','hu_clean_base_required','hu_candidate_too_large'})
        code=1 if error_code in conflicts or isinstance(error,OSError) else 2
        if code==1:
            result['status']='blocked'
    if json_mode:
        print(json.dumps(result,ensure_ascii=True,sort_keys=True))
    else:
        print(f"{result['command']}: {result['status']}")
        if 'applicable' in result:
            print(f"  Aplicable: {result['applicable']}")
        plan_hash=result.get('plan_sha256') or result.get('plan',{}).get('plan_sha256')
        if plan_hash:
            print(f'  SHA256 plan: {plan_hash}')
        for field in ('application_status','recovery_status','run_id'):
            if field in result:
                print(f'  {field}: {result[field]}')
        if result['command']=='onboard':
            for field in ('prepared','supervised_preparation_accepted','certified','remote_not_checked'):
                if field in result: print(f'  {field}: {result[field]}')
            for question in result.get('questions',[]):
                print(f"  Decisión requerida: {question['field']} ({question['reason']})")
        if result['command']=='hu' and 'run' in result:
            print(f"  HU: {result['run']['story_id']} ({result['run']['state']})")
            print(f"  Publicación permitida: {result['publication_allowed']}")
        if 'identities' in result:
            print('  Identidades: '+json.dumps(result['identities'],ensure_ascii=True,sort_keys=True))
        for name,value in result.get('input_hashes',{}).items():
            print(f'  SHA256 entrada {name}: {value}')
        for check in result['checks']:
            if 'gate' in check:
                print(f"  {check['gate']}: {check['status']} ({check['reason'] or 'checked'})")
                continue
            print(f"  {check['id']}: {check['status']} ({check.get('code','observation')}) — {check.get('message','Comprobación Desktop declarada.')}")
            for field in ('observed_version','observed_branch','remediation','document','fields'):
                if check.get(field):
                    print(f'    {field}: {check[field]}')
        for action in result.get('actions',[]):
            print(f"  {action['status']}: {action['path'] or action['kind']} — {action['reason']}")
            if 'sha256' in action:
                print(f"    SHA256 propuesta: {action['sha256']}")
            if 'content' in action:
                print(action['content'])
        for operation in result.get('operations',[]):
            print(f"  {operation['state']}: {operation['scope']} {operation['path']}")
    return code
