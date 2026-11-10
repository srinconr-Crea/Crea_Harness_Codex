"""Resolución limitada de plantillas revisadas; no shell ni entorno expandible."""
import copy
from pathlib import Path
import re
from .common import digest,safe_path
from . import git_adapter

def expand(token,variables):
    found=re.findall(r'\{([^{}]+)\}',token)
    if '{' in re.sub(r'\{[^{}]+\}','',token) or '}' in re.sub(r'\{[^{}]+\}','',token): raise ValueError('INVALID_TEMPLATE')
    if not found: return token
    # Reviewed path tokens and recognized report flag positions only.
    if token not in ('{junit_path}','{inventory_path}') and token!='--cov-report=json:{coverage_path}' and not any(token==f+'={'+v+'}' for f,v in [('--junitxml','junit_path'),('--crea-inventory','inventory_path')]):
        raise ValueError('TEMPLATE_POSITION_NOT_ALLOWED')
    if any(x not in variables or variables[x] is None for x in found): raise ValueError('TEMPLATE_VARIABLE_NOT_ALLOWED')
    return token.format(**variables)

def resolve(root,policy,settings,change,attempt,selected):
    if 'attempt_templates' not in settings: return policy,settings,None
    if not all(isinstance(x,str) and re.fullmatch(r'[A-Za-z0-9_-]+',x) for x in (change,attempt)): raise ValueError('SAFE_CHANGE_AND_ATTEMPT_REQUIRED')
    original_policy,original_settings=policy,settings
    policy=copy.deepcopy(policy); settings=copy.deepcopy(settings); templates=settings.pop('attempt_templates')
    directory=templates['evidence_dir'].format(change=change,attempt=attempt)
    safe_path(root,directory)
    outputs=[directory+'/'+name for name in ('plan.json','git.json','resultados.json','gate.json')]
    settings['checks']={name:cfg for name,cfg in settings['checks'].items() if name in selected}
    for check in policy['checks']:
        name=check['id']
        if name not in selected: continue
        if not re.fullmatch(r'[A-Za-z0-9_-]+',name): raise ValueError('UNSAFE_CHECK_ID')
        variables={'change':change,'attempt':attempt,'check_id':name,'evidence_dir':directory}
        for key in ('junit_path','inventory_path','coverage_path'):
            value=templates[key]
            variables[key]=value.format(**variables) if value else None
        config=settings['checks'].get(name)
        if config is None: continue
        for key in ('junit_path','inventory_path','coverage_path'): config[key]=variables[key]
        check['argv']=[expand(token,variables) for token in check['argv']]
        # An exact flag value can also be supplied as the following token.
        for pos,token in enumerate(original_policy['checks'][policy['checks'].index(check)]['argv']):
            if token in ('{junit_path}','{coverage_path}','{inventory_path}'):
                expected={'{junit_path}':'--junitxml','{coverage_path}':'--cov-report','{inventory_path}':'--crea-inventory'}[token]
                if pos<1 or check['argv'][pos-1]!=expected: raise ValueError('TEMPLATE_POSITION_NOT_ALLOWED')
        outputs += [v for k,v in variables.items() if k.endswith('_path') and v]
        outputs += [directory+'/'+prefix+name+suffix for prefix,suffix in [('receipt-','.json'),('stdout-','.log'),('stderr-','.log')]]
    settings['outputs']=sorted(outputs)
    git_adapter.validate_outputs(settings['outputs'])
    paths=[safe_path(root,x) for x in settings['outputs']]
    if len({str(p).casefold() for p in paths})!=len(paths): raise ValueError('OUTPUT_ALIAS_COLLISION')
    for path in paths:
        if path.exists() and path.stat().st_nlink>1: raise ValueError('OUTPUT_HARDLINK_ALIAS')
    for check in policy['checks']:
        from fnmatch import fnmatchcase
        if any(fnmatchcase(out,pat) for out in settings['outputs'] for pat in check['inputs']): raise ValueError('GENERATED_OUTPUT_IS_A_CHECK_INPUT')
    resolution={'schema_version':'1.0','change':change,'attempt':attempt,'source_policy_digest':digest(original_policy),'source_execution_digest':digest(original_settings),
                'resolved_policy_digest':digest(policy),'resolved_execution_digest':digest(settings)}
    return policy,settings,resolution
