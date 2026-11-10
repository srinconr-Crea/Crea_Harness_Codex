"""Observación estática. Ninguna importación cliente ni colección de pytest."""
import configparser
from fnmatch import fnmatchcase
import os
from pathlib import Path
import re
import tomllib

from .common import contract, digest, file_hash, read, safe_path
from . import git_adapter, schemas

EXCLUDED={'.git','.venv','venv','node_modules','site-packages','__pycache__','upstream','vendor','.agents','.codex','resources','.test-work','.pytest_cache'}
CONFIGS=('pytest.ini','setup.cfg','pyproject.toml','tox.ini','package.json')


def names(root):
    """Directory names only; never open test bodies, links or secret files."""
    for parent, dirs, files in os.walk(root, followlinks=False):
        dirs[:]=sorted(d for d in dirs if d not in EXCLUDED and not d.startswith('.')
                       and not (Path(parent)/d).is_symlink()
                       and not getattr(Path(parent)/d,'is_junction',lambda:False)())
        for name in sorted(files):
            p=Path(parent)/name
            if p.is_symlink() or getattr(p,'is_junction',lambda:False)(): continue
            if name.startswith('.') or re.search(r'(?i)(secret|credential|password|token|\.pem$)',name): continue
            yield p.relative_to(root).as_posix()


def is_test(name, locations):
    if any(x['kind']=='tests' and (name.startswith(x['path'].rstrip('/')+'/') or fnmatchcase(name,x['path'])) for x in locations):
        return name.endswith('.py') and Path(name).name!='conftest.py'
    return bool(re.fullmatch(r'(?:.*/)?(?:test_[^/]+|[^/]+_test)\.py',name))


def baseline(paths, policy, tools=()):
    """Proposals only. Existing reviewed equivalents suppress duplication."""
    result=[]
    families=[('documents',any(p.endswith(('.md','.json','.yaml','.yml','.toml')) for p in paths), 'local format/references; no business oracle'),
              ('python',any(p.endswith('.py') for p in paths),'AST syntax without import; no business oracle'),
              ('sql',any(p.endswith('.sql') for p in paths),'reviewed parser/dialect; no SQL/Delta runtime semantics'),
              ('notebook',any(p.endswith('.ipynb') for p in paths),'format/outputs/confidentiality; no notebook execution')]
    for technology,present,limit in families:
        if present:
            equivalent=any(c['configured'] and technology in c['criteria'] for c in policy['checks'])
            result.append({'technology':technology,'status':'equivalent' if equivalent else 'pending_tool' if technology=='sql' and 'sql_parser' not in tools else 'proposed',
                           'limit':limit,'materialize':not equivalent and technology!='sql'})
    return result


def associations(policy,name):
    return sorted({c for row in policy.get('lifecycle',{}).get('test_inventory',[])
                   if row['state']=='active' and fnmatchcase(name,row['pattern']) for c in row['check_ids']})


def discover(root, policy, tools=()):
    schemas.validate('policy',policy); contract.validate_policy(policy)
    root=Path(root).resolve(); paths=list(names(root)); configs=[]; locations=policy.get('lifecycle',{}).get('locations',[])
    observed_locations=list(locations)
    for name in CONFIGS:
        p=safe_path(root,name)
        if not p.is_file(): continue
        status='discovered'; declared=[]; commands=[]
        try:
            if name=='pyproject.toml':
                data=tomllib.loads(p.read_text(encoding='utf-8-sig'))
                cfg=data.get('tool',{}).get('pytest',{}).get('ini_options',{})
                declared=cfg.get('testpaths',[])
                if not cfg: status='unsupported'
            elif name=='package.json':
                data=read(p); commands=[{'name':k,'argv_observed':v,'execution':'not_run'} for k,v in sorted(data.get('scripts',{}).items()) if 'test' in k]
                status='unsupported'
            else:
                data=configparser.ConfigParser(interpolation=None); data.read_string(p.read_text(encoding='utf-8-sig'))
                section='pytest' if name=='pytest.ini' else 'tool:pytest'
                declared=data.get(section,'testpaths',fallback='').split()
                if name=='tox.ini': status='unsupported'
            if isinstance(declared,str): declared=declared.split()
            if not isinstance(declared,list) or any(not isinstance(x,str) for x in declared): raise ValueError('INVALID_TESTPATHS')
            for name2 in declared:
                safe_path(root,name2)
                observed_locations.append({'path':name2,'kind':'tests'})
        except (ValueError,TypeError,configparser.Error): status='unsupported'
        configs.append({'path':name,'sha256':file_hash(p),'status':status,'commands':commands})
    rows=[]
    for name in paths:
        if is_test(name,observed_locations) or Path(name).name=='conftest.py':
            checks=associations(policy,name)
            rows.append({'path':name,'status':'registered' if checks else 'unregistered','check_ids':checks,
                         'surface':'kit' if name.startswith('tests/crea/') else 'agent_evals' if any(x['kind']=='evals' and name.startswith(x['path'].rstrip('/')+'/') for x in locations) else 'project',
                         'reason':'reviewed pattern' if checks else 'association pending; collection requires reviewed Tester execution'})
    return {'schema_version':'1.0','action':'discover','execution':'not_run','rows':rows,'configs':configs,
            'partial':any(c['status']=='unsupported' for c in configs),'baseline':baseline(paths,policy,tools),
            'limitations':['metadata discovery; dynamic nodeids unknown','kit tests and installed dependencies excluded; no execution result']}


def reconcile(root,policy,base,outputs=(),moves=()):
    schemas.validate('policy',policy); contract.validate_policy(policy)
    git=git_adapter.collect(root,base,list(outputs)); locations=policy.get('lifecycle',{}).get('locations',[]); rows=[]
    for change in git['changes']:
        name,old=change['path'],change['old_path']
        if not is_test(name,locations) and not (old and is_test(old,locations)): continue
        checks=associations(policy,name)
        status='moved' if old else 'retirement_candidate' if change['status']=='D' else 'changed' if change['status']=='M' else 'registered' if checks else 'unregistered'
        rows.append({**change,'status':status,'git_status':change['status'],'check_ids':checks,
                     'reason':'reviewed association; execution inclusion still required' if checks else 'principal reconciliation pending; Reviewer decides semantic retirement'})
    for row in policy.get('lifecycle',{}).get('test_inventory',[]):
        if row['state']=='active' and not any(c in {x['id'] for x in policy['checks']} for c in row['check_ids']):
            raise ValueError('ACTIVE_INVENTORY_UNKNOWN_CHECK')
        if row['state']=='retired':
            from .common import resolve_reference
            resolve_reference(root,row['retirement']['decision_ref'],moves)
    return {'schema_version':'1.0','action':'reconcile','execution':'not_run','rows':sorted(rows,key=lambda x:(x['path'],x.get('old_path') or '')),
            'git_input_digest':git['input_digest'],'base':git['base_sha'],'partial':False}


def expected(policy,selected):
    result={x:{'files':[],'nodeids':[],'complete_files':[]} for x in selected}
    for row in policy.get('lifecycle',{}).get('test_inventory',[]):
        if row['state']!='active': continue
        for name in set(row['check_ids']).intersection(result):
            for source,target in [('expected_files','files'),('expected_nodeids','nodeids'),('complete_files','complete_files')]:
                result[name][target]=sorted(set(result[name][target]+row.get(source,[])))
    return result


def save(root,name,report):
    if not re.fullmatch(r'docs/hu/[A-Za-z0-9_-]+/handoffs/(?:planificacion|implementacion|pruebas|revision)-[1-9][0-9]*-inventory\.json',name):
        raise ValueError('INVENTORY_REPORT_DESTINATION_NOT_ALLOWED')
    p=safe_path(root,name)
    if p.exists(): raise ValueError('INVENTORY_REPORT_EXISTS')
    p.parent.mkdir(parents=True,exist_ok=True)
    import json
    with p.open('x',encoding='utf-8') as stream: json.dump(report,stream,ensure_ascii=False,indent=2)


def materialize_baseline(root, paths, destination, equivalent=False):
    """Only explicit authorized setup; no automatic writes from inspection."""
    from .common import ASSETS
    if equivalent: return {'status':'equivalent','written':False}
    target=safe_path(root,destination)
    if target.suffix!='.py' or target.exists(): raise ValueError('NEW_REVIEWED_PYTHON_TEST_DESTINATION_REQUIRED')
    chosen=sorted(set(name for name in paths if Path(name).suffix in ('.py','.json','.toml','.md','.ipynb')))
    for name in chosen:
        if not safe_path(root,name).is_file(): raise ValueError('BASELINE_INPUT_MISSING')
        if name==destination: raise ValueError('BASELINE_SELF_INPUT')
    if not chosen: return {'status':'pending_applicable_inputs','written':False}
    template=(ASSETS/'test_validaciones_tecnicas.py.template').read_text(encoding='utf-8')
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('x',encoding='utf-8') as stream: stream.write(template.replace('__CREA_REVIEWED_FILES__',repr(chosen)))
    return {'status':'materialized_not_run','written':True,'path':destination,'inputs':chosen,'limitations':['syntax/format/references only','SQL parser and business/runtime oracles remain pending']}


def review(root,policy,handoff):
    """Optional metadata conditions; execution obligations remain technical gates."""
    if 'lifecycle' not in policy: return []
    observation=reconcile(root,policy,handoff['scope']['base'] or 'HEAD',moves=handoff['scope']['moves'])
    data=handoff['evidence'].get('test_inventory_review')
    findings=[]
    affected={r['path'] for r in observation['rows']}
    if not data or not data['reconciled'] or not affected.issubset(set(data['affected'])) or any(r['status']=='unregistered' for r in observation['rows']):
        findings.append({'condition_id':'TEST_INVENTORY_RECONCILED','reason':'TEST_INVENTORY_RECONCILIATION_PENDING','owner':'principal'})
    dispositions={d['id']:d for d in (data or {}).get('dispositions',[])}
    for change in observation['rows']:
        lost=change['git_status']=='D' or (change.get('old_path') and associations(policy,change['old_path'])!=associations(policy,change['path']))
        if not lost: continue
        old=change.get('old_path') or change['path']
        for row in policy['lifecycle']['test_inventory']:
            if row['state']!='active' or not fnmatchcase(old,row['pattern']): continue
            d=dispositions.get(row['id'])
            if not d or d['action'] not in ('retire','replace'):
                findings.append({'condition_id':'TEST_RETIREMENT_REVIEWED','reason':'AFFECTED_TEST_REMOVAL_REQUIRES_REVIEWED_DISPOSITION','owner':'reviewer'})
            else:
                from .common import resolve_reference
                resolve_reference(root,d['decision_ref'],handoff['scope']['moves'])
    for row in policy['lifecycle']['test_inventory']:
        if row['state']!='retired': continue
        impacted=any(fnmatchcase(name,row['pattern']) for change in observation['rows'] for name in (change['path'],change.get('old_path')) if name)
        if not impacted and row['id'] not in dispositions and row['id'] not in (data or {}).get('affected',[]): continue
        d=dispositions.get(row['id'])
        if not d or d['action'] not in ('retire','replace') or d['decision_ref']!=row['retirement']['decision_ref']:
            findings.append({'condition_id':'TEST_RETIREMENT_REVIEWED','reason':'REVIEWED_RETIREMENT_DISPOSITION_PENDING','owner':'reviewer'})
        else:
            from .common import resolve_reference
            resolve_reference(root,d['decision_ref'],handoff['scope']['moves'])
    return findings
