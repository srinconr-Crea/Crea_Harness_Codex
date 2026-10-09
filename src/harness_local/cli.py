import argparse
import json
import sys

from harness_core.configuration import ConfigError
from . import __version__
from .diagnostics import Check, doctor
from .onboarding import preview


class Parser(argparse.ArgumentParser):
    def error(self,message):
        raise ConfigError('invalid_arguments')


def main(argv=None):
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    argv=list(sys.argv[1:] if argv is None else argv)
    parser=Parser(prog='harness',description='Diagnóstico y preview local, sin onboarding aplicado.')
    parser.add_argument('--version',action='version',version=__version__)
    commands=parser.add_subparsers(dest='command',required=True)
    for name in ('doctor','init'):
        p=commands.add_parser(name)
        p.add_argument('--path')
        p.add_argument('--policy')
        p.add_argument('--binding')
        p.add_argument('--json',action='store_true')
        if name=='init':
            p.add_argument('--dry-run',action='store_true')
            p.add_argument('--repo')
            p.add_argument('--base-branch')
    command='init' if 'init' in argv else 'doctor'
    json_mode='--json' in argv
    try:
        args=parser.parse_args(argv)
        if args.command=='init':
            if not args.dry_run:
                raise ConfigError('apply_not_supported')
            if not args.path or not args.policy or not args.binding:
                raise ConfigError('configuration_inputs_required')
            result,code=preview(args.path,args.policy,args.binding,args.repo,args.base_branch)
        else:
            result,code=doctor(args.path,args.policy,args.binding)
    except (ConfigError, OSError, UnicodeError) as error:
        error_code=error.code if isinstance(error,ConfigError) else 'local_read_error'
        result=dict(schema_version=1,command=command,status='invalid',checks=[vars(Check('input','error',error_code,'Entrada o configuración inválida.'))])
        if isinstance(error,ConfigError) and error.document:
            result['checks'][0].update(document=error.document,fields=error.fields)
        code=2
    if json_mode:
        print(json.dumps(result,ensure_ascii=True,sort_keys=True))
    else:
        print(f"{result['command']}: {result['status']}")
        if 'identities' in result:
            print('  Identidades: '+json.dumps(result['identities'],ensure_ascii=True,sort_keys=True))
        for name,value in result.get('input_hashes',{}).items():
            print(f'  SHA256 entrada {name}: {value}')
        for check in result['checks']:
            print(f"  {check['id']}: {check['status']} ({check['code']}) — {check['message']}")
            for field in ('observed_version','observed_branch','remediation','document','fields'):
                if check.get(field):
                    print(f'    {field}: {check[field]}')
        for action in result.get('actions',[]):
            print(f"  {action['status']}: {action['path'] or action['kind']} — {action['reason']}")
            if 'sha256' in action:
                print(f"    SHA256 propuesta: {action['sha256']}")
            if 'content' in action:
                print(action['content'])
    return code
