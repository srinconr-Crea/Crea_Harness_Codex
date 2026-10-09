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
    command=next((c for c in ('init','recover','doctor','integrate','desktop-check') if c in argv),'doctor')
    json_mode='--json' in argv
    try:
        args=parser.parse_args(argv)
        if args.command=='integrate':
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
                   'model_unavailable','effort_unavailable','integration_failed'}
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
        if 'identities' in result:
            print('  Identidades: '+json.dumps(result['identities'],ensure_ascii=True,sort_keys=True))
        for name,value in result.get('input_hashes',{}).items():
            print(f'  SHA256 entrada {name}: {value}')
        for check in result['checks']:
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
