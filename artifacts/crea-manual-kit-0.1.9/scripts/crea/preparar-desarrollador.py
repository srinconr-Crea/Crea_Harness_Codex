"""Preparación C: inspect no instala/autentica; bind requiere operación local explícita."""
import argparse
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
from subprocess import TimeoutExpired

from entorno_local import binding, databricks_profile
from team_common import (CONTRACTS, digest, exclusive, file_hash, git, process,
                         read, redact, safe_path, utc)


def read_failure(response, kind):
    # Classify known failures without persisting provider output or credentials.
    message=response.stderr.decode('utf-8',errors='replace').lower()
    denied=('permission denied','access denied','unauthorized','forbidden','authentication failed',
            'http 403','http 401','status code: 403','status code: 401','az login')
    network=('could not resolve','unable to connect','connection','network','timed out','timeout',
             'name or service not known','certificate verify')
    status='access_denied' if any(x in message for x in denied) else 'connection_error' if any(x in message for x in network) else 'unverified'
    return {'kind':kind,'status':status,'reason':'READ_'+status.upper()}


def checked_read(argv, root, kind, expected_repository=None):
    try:
        response=process(argv,root=root)
        if response.returncode:
            return read_failure(response,kind)
        data=json.loads(response.stdout)
        if not isinstance(data,dict):raise ValueError('READ_RESPONSE_NOT_OBJECT')
        if expected_repository:
            from entrega import repository_key
            if repository_key(data.get('remoteUrl','')) != repository_key(expected_repository):
                return {'kind':kind,'status':'unverified','reason':'REPOSITORY_IDENTITY_MISMATCH'}
        # No copy of raw account/workspace responses or credentials into diagnostics.
        return {'kind':kind,'status':'verified','scope':'read_only'}
    except TimeoutExpired:
        return {'kind':kind,'status':'connection_error','reason':'READ_TIMEOUT'}
    except (OSError,ValueError,KeyError,TypeError):
        return {'kind':kind,'status':'unverified','reason':'READ_NOT_AVAILABLE'}


def online_checks(root, project):
    from entrega import resolve, verified_remote, remote_sha
    repo=project['project']['repository']; rows=[]
    try:
        selected=verified_remote(root,project)
        sha,status=remote_sha(root,selected['remote'],selected['base_branch'])
        rows.append({'kind':'git_repository','status':status,'scope':'read_only'})
    except TimeoutExpired:
        rows.append({'kind':'git_repository','status':'connection_error','reason':'READ_TIMEOUT'})
    except (ValueError,OSError,KeyError):
        rows.append({'kind':'git_repository','status':'unverified','reason':'REMOTE_NOT_VERIFIED'})
    if repo.get('provider')=='azure_devops':
        values=[repo.get(k) for k in ('organization','project','name_or_id')]
        if all(values):
            argv=['az','repos','show','--organization',values[0],'--project',values[1],
                  '--repository',values[2],'--detect','false','--output','json']
            rows.append(checked_read(argv,root,'azure_repository',repo['url']))
        else: rows.append({'kind':'azure_repository','status':'unverified','reason':'CANONICAL_DESTINATION_REQUIRED'})
    if project.get('databricks',{}).get('enabled'):
        profile=databricks_profile(root,project)
        if profile and project['databricks'].get('workspace_host'):
            # Describe verifies configured host; current-user establishes only a read.
            try:
                described=process(['databricks','auth','describe','--profile',profile,'--output','json'],root=root)
                if described.returncode:
                    rows.append(read_failure(described,'databricks_identity'))
                else:
                    data=json.loads(described.stdout)
                    if not isinstance(data,dict) or not isinstance(data.get('config',{}),dict):
                        raise ValueError('PROFILE_RESPONSE_NOT_OBJECT')
                    configured=data.get('config',{}).get('host') or data.get('host')
                    if configured!=project['databricks']['workspace_host']:
                        raise ValueError('HOST_NOT_VERIFIED')
                    rows.append(checked_read(['databricks','current-user','me','--profile',profile,'--output','json'],root,'databricks_identity'))
            except TimeoutExpired:
                rows.append({'kind':'databricks_identity','status':'connection_error','reason':'READ_TIMEOUT'})
            except (ValueError,OSError,TypeError):
                rows.append({'kind':'databricks_identity','status':'unverified','reason':'HOST_OR_PROFILE_NOT_VERIFIED'})
        else: rows.append({'kind':'databricks_identity','status':'unverified','reason':'EXPLICIT_PROFILE_AND_HOST_REQUIRED'})
    return {'operations':rows,'write_permissions_verified':False}


def inspect_environment(root, online=False):
    root=Path(root).resolve()
    report={'schema_version':'1.0','kind':'developer_diagnostic','observed_at':utc(),
            'status':'partial','revision':None,'branch':None,'tools':[], 'pending':[],
            'remote':{'status':'not_run','write_permissions_verified':False},
            'native_agents_observed':False,'native_hooks_observed':False,'contracts':CONTRACTS}
    def pending(code,action,blocking=False):
        report['pending'].append({'code':code,'action':action,'blocking':blocking})
    project=read(safe_path(root,'docs/proyecto.json'))
    report['configuration_sha256']=file_hash(safe_path(root,'docs/proyecto.json'))
    report['system']={'platform':sys.platform,'os_name':os.name}
    report['checkout_remote']={'status':'unverified'}
    try:
        from entrega import verified_remote,repository_key
        selected=verified_remote(root,project)
        report['checkout_remote']={'name':selected['remote'],'repository':list(repository_key(project['project']['repository']['url'])),
                                   'status':'verified_local_identity'}
    except (ValueError,OSError,KeyError,TimeoutExpired):
        pending('GIT_REMOTE_NOT_VERIFIED','Reconciliar remoto local y repositorio compartido sin contactar servicios',True)
    selected_python=sys.executable
    try:
        if Path(git(root,'rev-parse','--show-toplevel')).resolve()!=root:
            raise ValueError('NOT_REPOSITORY_ROOT')
        report['revision']=git(root,'rev-parse','HEAD')
        report['branch']=git(root,'branch','--show-current')
        personal = git(root,'ls-files','--','.crea/local.json','.crea/local.json.new','.crea/diagnosticos','.crea/tmp')
        if personal:
            pending('PERSONAL_FILE_TRACKED','El archivo sigue rastreado; proponer retirada revisada, sin git rm automático')
    except (ValueError,OSError): pending('GIT_CHECKOUT_NOT_VERIFIED','Verificar checkout/HEAD sin reset o init',True)
    if not project['project'].get('setup_complete'):
        pending('PROJECT_SETUP_INCOMPLETE','Responsable debe completar onboarding compartido fuera de C',True)
    testing=project['validation']['testing']
    try:
        policy=read(safe_path(root,testing['policy_path']))
        execution=read(safe_path(root,testing['execution_path']))
        if not policy.get('setup_complete') or not policy.get('checks'):
            pending('POLICY_NOT_READY','Reconciliar catálogo compartido sin editarlo desde C',True)
        if execution.get('reviewed_policy_digest')!=digest(policy):
            pending('POLICY_REVIEW_NOT_CURRENT','Responsable debe revisar catálogo',True)
        if execution.get('local_environment_path'):
            from entorno_local import resolve
            try: selected_python=resolve(root,execution)['python_executable']
            except (ValueError,OSError): pending('LOCAL_BINDING_REQUIRED','Elegir Python y ejecutar bind autorizado')
        elif execution.get('python_executable'):
            selected_python=execution['python_executable']
    except (ValueError,OSError,KeyError): pending('TESTING_CONFIGURATION_MISSING','Reconciliar configuración compartida',True)
    if not (safe_path(root,'openspec/config.yaml').is_file() or safe_path(root,'openspec/config.yml').is_file()):
        pending('OPENSPEC_NOT_CONFIGURED','Onboarding compartido pendiente; no ejecutar init desde C',True)
    for item in project.get('inventory',{}).get('paths',[]):
        if item.get('exists') and not safe_path(root,item['path'].rstrip('/')).exists():
            pending('SHARED_RESOURCE_MISSING','Reconciliar inventario y recursos compartidos: '+item['path'],True)
    dependencies={'yaml':'PyYAML','jsonschema':'jsonschema','pytest':'pytest','rfc3339_validator':'rfc3339-validator'}
    report['selected_python']=selected_python
    try:
        probe = process([selected_python,'-I','-B','-c',
            'import importlib.util,json,sys; print(json.dumps({"version":sys.version,"missing":[m for m in ["yaml","jsonschema","pytest","rfc3339_validator"] if importlib.util.find_spec(m) is None]}))'],root=root,timeout=10)
        if probe.returncode: raise ValueError('INTERPRETER_PROBE_FAILED')
        python_details=json.loads(probe.stdout)
        missing=python_details['missing']; report['python_version']=python_details['version']
    except (OSError,ValueError,TimeoutExpired):
        missing=list(dependencies);pending('LOCAL_INTERPRETER_NOT_VERIFIED','Revisar el intérprete elegido sin instalarlo implícitamente')
    host_missing=[module for module in dependencies if importlib.util.find_spec(module) is None]
    if missing or host_missing:
        pending('VALIDATION_DEPENDENCY_UNAVAILABLE','Usar intérprete preparado o autorizar dependencias; elegido: '
                +', '.join(missing)+'; proceso de diagnóstico: '+', '.join(host_missing))
    else:
        try:
            from testing.kit_validation import validate_kit
            validate_kit(root)
        except (ValueError,OSError,KeyError,TypeError,ImportError):
            pending('SHARED_VALIDATION_NOT_SATISFIED','Revisar configuración y consumidores sin sobrescribirlos',True)
    tools=['git','node','openspec.cmd' if os.name=='nt' else 'openspec']
    if project['project']['repository'].get('provider')=='azure_devops': tools.append('az')
    if project.get('databricks',{}).get('enabled'): tools.append('databricks')
    for name in tools:
        binary=shutil.which(name)
        row={'name':name,'available':bool(binary),'version':None}
        if binary:
            try:
                result=process([binary,'--version'],root=root,timeout=10)
                if result.returncode==0: row['version']=redact(result.stdout.decode('utf-8',errors='replace').strip())[:512]
                else: pending('TOOL_VERSION_NOT_VERIFIED','Comprobar versión de '+name)
            except (OSError,TimeoutExpired): pending('TOOL_VERSION_NOT_VERIFIED','Comprobar versión de '+name)
        else: pending('TOOL_UNAVAILABLE','Preparar '+name+' solo dentro del alcance autorizado')
        report['tools'].append(row)
    required_contracts={'entrega.py':['delivery_target'], 'compatibilidad.py':['target_compatibility'],
                        'preparar-desarrollador.py':['local_environment','projection']}
    for name,keys in required_contracts.items():
        helper=safe_path(root,'scripts/crea/'+name)
        if not helper.is_file():
            pending('CONSUMER_CONTRACT_NOT_VERIFIED','Actualizar consumidores mediante B, no C: '+name,True)
            continue
        try:
            result=process([sys.executable,'-B',str(helper),'--describe-contracts'],root=root,timeout=10)
            described=json.loads(result.stdout) if result.returncode==0 else {}
            if any(described.get(key)!=CONTRACTS[key] for key in keys): raise ValueError('contract')
        except (OSError,ValueError,TimeoutExpired): pending('CONSUMER_CONTRACT_NOT_VERIFIED','Revisar soporte efectivo de '+name,True)
    if online:
        report['remote']=online_checks(root,project)
        if any(x['status']!='verified' for x in report['remote']['operations']):
            pending('PERSONAL_CONNECTION_NOT_VERIFIED','Autenticación/MFA o permisos personales requieren intervención humana')
    elif project['project']['repository'].get('provider')!='unconfigured':
        pending('PERSONAL_CONNECTION_NOT_CHECKED','Ejecutar lecturas personales con --online cuando corresponda')
    report['status']='blocked' if any(x['blocking'] for x in report['pending']) else 'partial' if report['pending'] else 'ready'
    return report


def bind(root, python, profile=None, apply=False):
    root=Path(root).resolve(); path=safe_path(root,'.crea/local.json')
    proposed={'schema_version':'1.0','python_executable':str(python)}
    if profile is not None: proposed['databricks_profile']=profile
    if not Path(python).is_absolute() or not Path(python).is_file(): raise ValueError('LOCAL_INTERPRETER_REQUIRED')
    if profile is not None and (not profile.strip() or any(c in profile for c in '\r\n\0')): raise ValueError('LOCAL_PROFILE_INVALID')
    for parent in [Path(python),*Path(python).parents]:
        if parent.is_symlink() or getattr(parent,'is_junction',lambda:False)(): raise ValueError('LOCAL_INTERPRETER_LINK')
    before=binding(root) if path.exists() else None
    result={'status':'unchanged' if before==proposed else 'preview','before':before,'after':proposed}
    if before==proposed or not apply: return result
    path.parent.mkdir(parents=True,exist_ok=True)
    previous_hash=file_hash(path) if before else None
    temporary=safe_path(root,'.crea/local.json.new')
    with temporary.open('x',encoding='utf-8') as handle: handle.write(json.dumps(proposed,ensure_ascii=False,indent=2)+'\n')
    if (file_hash(path) if path.exists() else None)!=previous_hash: raise ValueError('LOCAL_BINDING_CHANGED_CONCURRENTLY')
    os.replace(temporary,path)
    result['status']='updated'
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['inspect','bind'],nargs='?'); p.add_argument('--describe-contracts',action='store_true')
    p.add_argument('--repo',type=Path); p.add_argument('--online',action='store_true'); p.add_argument('--out')
    p.add_argument('--python'); p.add_argument('--databricks-profile'); p.add_argument('--apply-local',action='store_true')
    args=p.parse_args()
    if args.describe_contracts: print(json.dumps(CONTRACTS)); return 0
    try:
        if not args.repo or not args.action: raise ValueError('EXPLICIT_REPO_AND_ACTION_REQUIRED')
        if args.action=='bind': value=bind(args.repo,args.python,args.databricks_profile,args.apply_local)
        else: value=inspect_environment(args.repo,args.online)
        if args.out: exclusive(args.repo,args.out,value,'.crea/diagnosticos/')
        print(json.dumps(value,ensure_ascii=False)); return 3 if value['status'] in ('partial','blocked') else 0
    except Exception as exc:
        # The dependency-free diagnostic must remain structured even with no site packages.
        print(json.dumps({'status':'partial','check_status':'validator_error','error':type(exc).__name__})); return 4


if __name__=='__main__': raise SystemExit(main())
