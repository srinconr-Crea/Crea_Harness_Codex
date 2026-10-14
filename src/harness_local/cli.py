import argparse
import json
import sqlite3
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
    setup=commands.add_parser('setup')
    setup.add_argument('action',choices=('interview','preview','apply','status','recover'))
    for field in ('input','plan','plan-out','authorize'): setup.add_argument('--'+field)
    setup.add_argument('--json',action='store_true')
    bootstrap=commands.add_parser('bootstrap')
    bootstrap.add_argument('--json',action='store_true')
    release=commands.add_parser('release')
    release.add_argument('action',choices=('candidate','gate'))
    release.add_argument('--input')
    release.add_argument('--evidence-root')
    release.add_argument('--json',action='store_true')
    update=commands.add_parser('update')
    update.add_argument('action',choices=('preview','apply','recover'))
    for field in ('path','policy','binding','input','plan','plan-out'):
        update.add_argument('--'+field)
    update.add_argument('--apply',action='store_true')
    update.add_argument('--json',action='store_true')
    story=commands.add_parser('story')
    story.add_argument('action',choices=('read','bind'))
    for field in ('provider','source','input','path','policy','binding'):
        story.add_argument('--'+field)
    story.add_argument('--json',action='store_true')
    pr=commands.add_parser('pr')
    pr.add_argument('action',choices=('preview','publish','reconcile'))
    pr.add_argument('--input',required=True)
    for field in ('path','policy','binding','provider','out'):
        pr.add_argument('--'+field)
    pr.add_argument('--json',action='store_true')
    evaluation=commands.add_parser('eval')
    evaluation.add_argument('action',choices=('validate','run','report'))
    evaluation.add_argument('--input',required=True)
    evaluation.add_argument('--json',action='store_true')
    usage=commands.add_parser('usage')
    usage.add_argument('action',choices=('report',))
    usage.add_argument('--input',required=True)
    usage.add_argument('--json',action='store_true')
    validation=commands.add_parser('validate')
    validation.add_argument('action',choices=('plan','static','worker','remote','bundle','gate','attach'))
    validation.add_argument('--input',required=True)
    validation.add_argument('--json',action='store_true')
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
    command=next((c for c in ('setup','bootstrap','release','update','story','pr','eval','usage','validate','hu','onboard','init','recover','doctor','integrate','desktop-check','review-snapshot','review-compare','supervised-prepare') if c in argv),'doctor')
    json_mode='--json' in argv
    try:
        args=parser.parse_args(argv)
        if args.command=='bootstrap':
            from .distribution import bootstrap
            result,code=bootstrap()
        elif args.command=='release':
            from .distribution import candidate_manifest, release_gate, report
            from harness_core.distribution import PilotReport
            from harness_core.onboarding_plan import load_json
            if args.action=='candidate':
                if args.input or args.evidence_root: raise ConfigError('invalid_arguments')
                result,code=report('release', 'partial', manifest=candidate_manifest().model_dump())
            else:
                if not args.input: raise ConfigError('invalid_arguments')
                result,code=release_gate(load_json(args.input,PilotReport),evidence_root=args.evidence_root)
        elif args.command=='setup':
            from . import environment_setup as environment
            from harness_core.configuration import load_document
            if args.action in ('interview','preview'):
                if not args.input or args.plan or args.authorize or (args.action=='interview' and args.plan_out):
                    raise ConfigError('invalid_input')
                value=load_document(args.input)
                if args.action=='interview':
                    result=environment.interview(value); code=2 if result['questions'] else 0
                else: result,code=environment.preview(value,plan_out=args.plan_out)
            else:
                if not args.plan or args.input or args.plan_out: raise ConfigError('invalid_input')
                if args.action=='status':
                    if args.authorize: raise ConfigError('invalid_input')
                    result,code=environment.status(args.plan)
                else:
                    if not args.authorize: raise ConfigError('invalid_input')
                    operation=environment.apply if args.action=='apply' else environment.recover
                    result,code=operation(args.plan,args.authorize)
        elif args.command=='update':
            from .distribution import preview as update_preview, apply as update_apply, recover as update_recover
            from harness_core.distribution import UpdateRequest
            from harness_core.onboarding_plan import load_json, separate
            if not args.path or not args.policy: raise ConfigError('invalid_arguments')
            if args.action=='preview':
                if not args.binding or not args.input or args.plan or args.apply: raise ConfigError('invalid_arguments')
                request=load_json(args.input,UpdateRequest)
                if args.plan_out:
                    separate([args.plan_out,args.input])
                result,code=update_preview(args.path,args.policy,args.binding,request.installation,
                    request.manifest,request.upstream,plan_out=args.plan_out)
            else:
                if not args.plan or args.binding or args.input or args.plan_out or (args.apply and args.action!='recover'):
                    raise ConfigError('invalid_arguments')
                if args.action=='apply': result,code=update_apply(args.path,args.policy,args.plan)
                else: result,code=update_recover(args.path,args.policy,args.plan,apply_changes=args.apply)
        elif args.command=='story':
            from harness_core.configuration import load_document
            from harness_core.story import ProviderBinding,StoryPlanBinding
            from .story_providers import select_provider
            if args.action=='read':
                if not args.provider or not args.source or any((args.input,args.path,args.policy,args.binding)): raise ConfigError('invalid_arguments')
                provider_binding=load_document(args.provider,ProviderBinding)
                provider=select_provider(provider_binding)
                snapshot=provider.read_story(provider_binding,args.source)
                result=dict(schema_version=1,command='story',status='ready',checks=[],snapshot=snapshot.model_dump(),
                    simulated=provider.simulated,certified=False,publication_allowed=False)
            else:
                if not all((args.input,args.path,args.policy,args.binding)) or any((args.provider,args.source)): raise ConfigError('invalid_arguments')
                from .hu import HuService
                from .publication import bind_story
                result=bind_story(HuService(args.path,args.policy,args.binding),load_document(args.input,StoryPlanBinding))
            code=0
        elif args.command=='pr':
            from .publication import PublicationRequest,PublicationService,preview as pr_preview,candidate_gate,parse
            from harness_core.configuration import load_document,safe_path
            from harness_core.story import ProviderBinding
            from harness_core.onboarding_plan import separate
            request=parse(PublicationRequest,load_document(args.input))
            if args.action=='preview':
                if args.out and not args.path: raise ConfigError('publication_target_required')
                protected=[p for p in (args.policy,args.binding,args.provider,args.input) if p]
                if args.binding:
                    from harness_core.contracts import Binding
                    protected.append(load_document(args.binding,Binding).state_dir)
                result=pr_preview(request.intent,request.authorization,request.evaluation,export=args.out,target=args.path,protected=protected)
                code=0
            else:
                if not all((args.path,args.policy,args.binding,args.provider)) or args.out: raise ConfigError('invalid_arguments')
                from .hu import HuService
                from .story_providers import select_provider
                hu_service=HuService(args.path,args.policy,args.binding)
                separate([str(safe_path(args.provider)),str(hu_service.target),str(hu_service.state)])
                provider_binding=load_document(args.provider,ProviderBinding)
                provider=select_provider(provider_binding,target=hu_service.target)
                if provider.simulated: raise ConfigError('publication_fixture_read_only')
                result=PublicationService(provider_binding,provider,hu_service.state,
                    candidate_check=lambda i:candidate_gate(hu_service,i)).publish(request.intent,request.authorization,request.evaluation)
                code=0 if result['status']=='published' else 1
        elif args.command in ('eval','usage'):
            from .observability_service import load_input, usage_report
            value=load_input(args.input)
            if args.command=='eval':
                from .evaluation_service import dispatch
                result,code=dispatch(args.action,value)
            else:
                result,code=usage_report(value),0
        elif args.command=='validate':
            from .validation_service import dispatch
            from harness_core.configuration import load_document
            result,code=dispatch(args.action,load_document(args.input))
        elif args.command=='hu':
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
    except (ConfigError, OSError, UnicodeError, sqlite3.Error) as error:
        error_code=error.code if isinstance(error,ConfigError) else 'local_state_error' if isinstance(error,sqlite3.Error) else 'local_read_error'
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
        conflicts.update({'validation_operation_conflict','validation_journal_version','validation_journal_conflict',
            'validation_journal_unavailable','remote_service_unavailable'})
        conflicts.update({'provider_tool_missing','provider_mcp_unavailable','provider_unavailable','provider_repository_mismatch',
            'provider_story_mismatch','provider_story_invalid','provider_capability_missing','publication_fixture_read_only'})
        conflicts.update({'story_plan_approval_required','story_plan_binding_mismatch','story_plan_binding_immutable',
            'story_source_conflict','story_source_version','context_changed'})
        conflicts.update({'update_identity_mismatch','update_drift','update_conflict','update_failed'})
        code=1 if error_code in conflicts or isinstance(error,(OSError,sqlite3.Error)) else 2
        if code==1:
            result['status']='blocked'
        if command=='setup':
            reason=error_code
            code= {'invalid_input':2,'identity_mismatch':2,'access_denied':3,'tool_unavailable':3,
                'skill_discovery_pending':3,'auth_pending':3,'permission_conflict':3,
                'plan_stale':4,'owned_resource_conflict':4,'download_integrity_failed':5,'recovery_required':6}.get(reason,2)
            result.update(status='blocked',reason=reason,certified=False,release_allowed=False,publication_allowed=False)
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
