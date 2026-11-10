"""Compatibilidad observacional: inspect puro, simulate aislado; jamás integra ramas."""
import argparse
from fnmatch import fnmatchcase
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

import entrega
from team_common import (CONTRACTS, digest, file_hash, git, git_result, hu_export,
                         identity, process, read, safe_path, utc, validate_data)
from testing import git_adapter


from contexto import consumer_impact


def excluded(project,name):
    patterns=project.get('inventory',{}).get('exclude_from_context',[])
    return any(name.startswith(p) if p.endswith('/') else fnmatchcase(name,p) for p in patterns)


def blob(root, revision, name, project, budget):
    safe_path(root,name)
    if excluded(project,name): raise ValueError('CONTEXT_PATH_EXCLUDED')
    if not re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}',revision):raise ValueError('EXACT_REVISION_REQUIRED')
    info=git_result(root,'ls-tree','-z',revision,'--',name)
    if info.returncode or not info.stdout:raise ValueError('DOCUMENT_NOT_PRESENT_AT_REVISION')
    mode=info.stdout.split(b' ',1)[0]
    if mode==b'120000':raise ValueError('DOCUMENT_LINK_NOT_ALLOWED')
    obj=revision+':'+name
    size=int(git(root,'cat-file','-s',obj))
    limits=project.get('context_management',{}).get('limits',{})
    if size>limits.get('per_document_bytes',262144) or budget[0]+size>limits.get('total_bytes',2097152):
        raise ValueError('CONTEXT_READ_LIMIT')
    result=git_result(root,'cat-file','blob',obj)
    if result.returncode:raise ValueError('DOCUMENT_READ_UNAVAILABLE')
    budget[0]+=size
    return result.stdout


def worktree_document(root, name, project, budget):
    path=safe_path(root,name)
    if excluded(project,name):raise ValueError('CONTEXT_PATH_EXCLUDED')
    if not path.is_file():raise ValueError('DOCUMENT_NOT_PRESENT_IN_CANDIDATE')
    limits=project.get('context_management',{}).get('limits',{})
    size=path.stat().st_size
    if size>limits.get('per_document_bytes',262144) or budget[0]+size>limits.get('total_bytes',2097152):
        raise ValueError('CONTEXT_READ_LIMIT')
    data=path.read_bytes()
    if len(data)!=size:raise ValueError('DOCUMENT_CHANGED_DURING_READ')
    budget[0]+=size
    return data


def referenced_documents(root, project, own, target, source_sha, target_sha, budget=None, change=None):
    paths=set()
    for row in project.get('context_management',{}).get('components',[]):
        if any(any(fnmatchcase(name,p) for p in row['paths']) for name in own+target):
            paths.update(d['path'] for d in row['documents'] if d.get('kind')!='history')
    current_specs='openspec/changes/'+identity(change)+'/specs/' if change else None
    paths.update(name for name in own+target if name.startswith(('openspec/specs/','docs/constituciones/'))
                 or (current_specs and name.startswith(current_specs))
                 or name in ('docs/proyecto.json','docs/contexto-proyecto.md'))
    refs=[];limits=[]
    if budget is None:budget=[0]
    for name in sorted(paths):
        for revision,observation in [(source_sha,'worktree'),(target_sha,'git')]:
            try:
                data=worktree_document(root,name,project,budget) if observation=='worktree' else blob(root,revision,name,project,budget)
                refs.append({'path':name,'revision':revision,'observation':observation,'sha256':hashlib.sha256(data).hexdigest()})
            except ValueError as exc:limits.append({'path':name,'revision':revision,'reason':str(exc)})
    return refs,limits


def simulation_identity(source_sha,target_sha):
    return {'source_sha':source_sha,'target_sha':target_sha}


def simulate(root, source_sha, snapshot, scratch):
    root=Path(root).resolve(); scratch=Path(scratch)
    if not scratch.is_absolute() or not scratch.is_relative_to(root):raise ValueError('EXPLICIT_LOCAL_SCRATCH_REQUIRED')
    relative=scratch.relative_to(root).as_posix()
    if not relative.startswith('.crea/tmp/'):raise ValueError('SCRATCH_OUTSIDE_ALLOWED_DIRECTORY')
    scratch=safe_path(root,relative)
    if scratch.exists():raise ValueError('SIMULATION_SCRATCH_OCCUPIED')
    if snapshot.get('status')!='verified' or not snapshot.get('objects_available'):raise ValueError('VERIFIED_TARGET_OBJECTS_REQUIRED')
    source=git(root,'rev-parse','--verify',source_sha+'^{commit}');target=git(root,'rev-parse','--verify',snapshot['target_sha']+'^{commit}')
    if source!=source_sha or target!=snapshot['target_sha']:raise ValueError('EXACT_REVISION_REQUIRED')
    env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    env.update({'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':os.devnull})
    scratch.parent.mkdir(parents=True,exist_ok=True)
    created=process(['git','init','--bare','--template=',str(scratch)],root=root,env=env)
    if created.returncode:raise ValueError('SIMULATION_INITIALIZATION_FAILED')
    objects=Path(git(root,'rev-parse','--git-path','objects'))
    if not objects.is_absolute():objects=root/objects
    env['GIT_ALTERNATE_OBJECT_DIRECTORIES']=str(objects.resolve())
    result=process(['git','--git-dir='+str(scratch),'-c','core.hooksPath='+str(scratch/'no-hooks'),
                    'merge-tree','--write-tree','--name-only','-z',target,source],root=root,env=env)
    status='clean' if result.returncode==0 else 'conflict' if result.returncode==1 else 'undetermined'
    values=result.stdout.split(b'\0'); names=[]
    if status=='conflict':
        for value in values[1:]:
            if not value:break
            names.append(value.decode('utf-8',errors='strict'))
    limits=[]
    if status=='undetermined':limits.append('SIMULATION_NOT_SUPPORTED_OR_FAILED')
    # Attributes are not executed. Non-default merge semantics need separate review.
    for revision in dict.fromkeys([source,target]):
        for token in git_result(root,'ls-tree','-rz','--name-only',revision).stdout.split(b'\0'):
            if token and Path(token.decode('utf-8')).name=='.gitattributes':
                limits.append('ATTRIBUTES_REQUIRE_REVIEW');break
    value={'schema_version':'1.0','kind':'git_integration_simulation','change':snapshot['change'],
           **simulation_identity(source,target),'status':status,'conflict_paths':sorted(set(names)),
           'limits':sorted(set(limits)),'combined_tests_executed':False}
    return value


def managed_artifact(root,name,definition,projection):
    """Only predeclared exact JSON observations may be excluded by content-v3."""
    path=safe_path(root,name)
    if not path.is_file():return False
    change=identity(projection['change'])
    if not re.fullmatch(r'docs/hu/'+re.escape(change)+r'/compatibilidad/attempt-[A-Za-z0-9_-]+/[A-Za-z0-9_-]+\.json',name):
        raise ValueError('COMPATIBILITY_ARTIFACT_PATH_INVALID')
    data=read(path)
    schemas={'git_target_snapshot':'git-target-snapshot','target_compatibility_report':'compatibilidad',
             'target_semantic_review':'compatibilidad-review','git_integration_simulation':'compatibilidad-simulation'}
    if definition['kind'] not in schemas or data.get('kind')!=definition['kind'] or data.get('change')!=change:
        raise ValueError('COMPATIBILITY_ARTIFACT_IDENTITY')
    validate_data(root,'docs/plantillas/'+schemas[definition['kind']]+'.schema.json',data)
    if data.get('functional_obligations'):
        return False
    if name in projection.get('history',{}) and file_hash(path)!=projection['history'][name]:
        raise ValueError('HISTORIC_COMPATIBILITY_CHANGED')
    return True


def local_identity(root,handoff):
    observation=git_adapter.observe(root)
    files=dict(observation['files'])
    projection={'change':handoff['identity']['change'],'history':{}}
    for definition in handoff['scope'].get('compatibility_artifacts',[]):
        name=definition['path']
        if name in files and managed_artifact(root,name,definition,projection):files.pop(name)
    return digest(files)


def inspect(root, project, handoff, snapshot, simulation=None, semantic_review=None, current_target=None):
    change=identity(handoff['identity']['change']);settings=entrega.resolve(project)
    head=git(root,'rev-parse','HEAD');source_branch=git(root,'branch','--show-current')
    birth=handoff['scope'].get('git_delivery',{}).get('branch_start_sha') or handoff['scope']['base']
    report={'schema_version':'1.0','kind':'target_compatibility_report','change':change,'observed_at':utc(),
            'source_sha':head,'source_branch':source_branch,'branch_start_sha':birth,'validation_base':handoff['scope']['base'],
            'target_sha':snapshot.get('target_sha'),'candidate_digest':handoff['scope'].get('candidate_digest'),
            'outcome':'undetermined','coverage':'partial','freshness':'unverified','dimensions':{},
            'findings':[],'limitations':[],'affected_consumers':[],'recommended_checks':[],
            'review_paths':[],'document_refs':[],'scope_digest':'','combined_tests_executed':False,
            'functional_obligations':[],'preserved_evidence':['Local plan/receipts remain subject to their existing gate'],
            'actions':[]}
    if not project['delivery'].get('compatibility',{}).get('enabled'):
        report['limitations'].append('COMPATIBILITY_NOT_ADOPTED');report['scope_digest']=digest({'disabled':True});return report
    entrega.validate_feature(project,source_branch)
    if (snapshot.get('change')!=change or snapshot.get('target_branch')!=settings['target_branch']
        or snapshot.get('remote')!=settings['remote']
        or snapshot.get('repository')!=list(entrega.repository_key(project['project']['repository']['url']))):
        raise ValueError('TARGET_SNAPSHOT_IDENTITY_MISMATCH')
    if snapshot.get('status')!='verified' or not snapshot.get('objects_available'):
        report['limitations'].append('TARGET_'+snapshot.get('status','unverified').upper())
        report['scope_digest']=digest(snapshot);report['actions']=['Comprobar destino sin crearlo o sustituirlo'];return report
    report['freshness']='current'
    if current_target:
        if any(current_target.get(key)!=snapshot.get(key) for key in ('change','repository','remote','target_branch')):
            raise ValueError('TARGET_RECHECK_IDENTITY_MISMATCH')
        report['freshness']='unverified' if current_target.get('status')!='verified' else 'current' if current_target.get('target_sha')==snapshot['target_sha'] else 'stale'
    try:
        ranges=entrega.ranges(root,birth,head,snapshot['target_sha'])
        local=git_adapter.collect(root,birth,[])['changes']
    except ValueError as exc:
        report['limitations'].append(str(exc));report['scope_digest']=digest(snapshot);return report
    report['ranges']=ranges
    names=lambda rows:sorted({n for row in rows for n in (row['path'],row['old_path']) if n})
    own=names(local);target=names(ranges['target_changes'])
    definitions={x['path'] for x in handoff['scope'].get('compatibility_artifacts',[])}
    own=[n for n in own if n not in definitions]
    impact=consumer_impact(project,target,own);report['impact']=impact
    reference_budget=[0]
    # Target-side architecture is observed, never silently adopted into the feature.
    try:
        payload=blob(root,snapshot['target_sha'],'docs/proyecto.json',project,reference_budget)
        target_project=json.loads(payload)
        if target_project.get('context_management')!=project.get('context_management'):
            target_impact=consumer_impact(target_project,target,own)
            report['target_context_impact']=target_impact
            impact['affected_consumers']=sorted(set(impact['affected_consumers']+target_impact['affected_consumers']))
            report['limitations'].append('TARGET_CONTEXT_CONFIGURATION_CHANGED')
    except ValueError as exc:
        if str(exc)!='DOCUMENT_NOT_PRESENT_AT_REVISION':report['limitations'].append(str(exc))
    report['affected_consumers']=impact['affected_consumers']
    refs,limits=referenced_documents(root,project,own,target,head,snapshot['target_sha'],reference_budget,change)
    report['document_refs']=refs;report['limitations']+=limits
    try: policy=read(safe_path(root,project['validation']['testing']['policy_path']))
    except (ValueError,OSError):policy={'checks':[],'rules':[]};report['limitations'].append('CATALOG_NOT_AVAILABLE')
    known_checks={row['id'] for row in policy['checks']}
    recommended_ids={key for rule in policy.get('rules',[])
                     if any(fnmatchcase(name,p) for name in target for p in rule['paths'])
                     for key in rule.get('checks',[])}
    try:
        target_policy=json.loads(blob(root,snapshot['target_sha'],project['validation']['testing']['policy_path'],project,reference_budget))
        recommended_ids.update(key for rule in target_policy.get('rules',[])
                               if any(fnmatchcase(name,p) for name in target for p in rule['paths'])
                               for key in rule.get('checks',[]))
    except (ValueError,KeyError,TypeError) as exc:
        if str(exc)!='DOCUMENT_NOT_PRESENT_AT_REVISION':report['limitations'].append('TARGET_CATALOG_NOT_AVAILABLE')
    for key in sorted(recommended_ids-known_checks):
        report['findings'].append({'type':'impact','reason':'UNKNOWN_RECOMMENDED_CHECK: '+key,'owner':'principal'})
    components={c['id']:c for c in project.get('context_management',{}).get('components',[])}
    consumer_paths=[p for key in impact['affected_consumers'] for p in components.get(key,{}).get('paths',[])]
    for check in policy['checks']:
        reasons=[]
        if any(fnmatchcase(name,pattern) for name in target for pattern in check['inputs']):reasons.append('target-input-changed')
        if any(fnmatchcase(name,p) or fnmatchcase(p,name) for name in consumer_paths for p in check['inputs']):reasons.append('affected-consumer')
        if any(check['id'] in rule.get('checks',[]) and any(fnmatchcase(name,p) for name in target for p in rule['paths']) for rule in policy.get('rules',[])):
            reasons.append('target-path-rule')
        if reasons:report['recommended_checks'].append({'check_id':check['id'],'reasons':sorted(set(reasons))})
    report['review_paths']=sorted(set(own+target+[r['path'] for r in refs]))
    report['scope_digest']=digest({'birth':birth,'source':head,'source_branch':source_branch,'target':snapshot['target_sha'],
                                  'local':local_identity(root,handoff),'project':project,'policy':policy,
                                  'impact':impact,'document_refs':refs})
    report['dimensions']={'git':'partial','dependencies':'complete' if impact['known'] and not impact['unknown_paths'] else 'partial',
                          'contracts':'not_run','documentation':'partial' if limits else 'complete','test_impact':'complete' if 'CATALOG_NOT_AVAILABLE' not in report['limitations'] else 'partial'}
    textual_conflict=False
    if simulation:
        if any(simulation.get(k)!=v for k,v in simulation_identity(head,snapshot['target_sha']).items()):raise ValueError('SIMULATION_IDENTITY_MISMATCH')
        textual_conflict=simulation['status']=='conflict'
        report['dimensions']['git']='complete' if simulation['status'] in ('clean','conflict') and not simulation['limits'] else 'partial'
        report['limitations']+=simulation['limits']
        if textual_conflict:report['findings'].append({'type':'git','reason':'TEXTUAL_CONFLICT','paths':simulation['conflict_paths'],'owner':'developer'})
        pending=git_adapter.collect(root,head,[])['changes']
        if any(row['path'] not in definitions or row.get('old_path') and row['old_path'] not in definitions for row in pending):
            report['dimensions']['git']='partial'
            report['limitations'].append('SIMULATION_COVERS_HEAD_ONLY')
    if ranges['inherited_commits']:
        report['findings'].append({'type':'scope','reason':'INHERITED_WORK_OUTSIDE_TARGET','owner':'principal','commits':ranges['inherited_commits']})
    if impact['affected_consumers'] or impact['shared_components'] or set(own)&set(target):
        report['findings'].append({'type':'impact','reason':'CONTRACT_OR_CONSUMER_REVIEW_REQUIRED','owner':'reviewer'})
    semantic_status=None
    if semantic_review:
        if (semantic_review.get('kind')!='target_semantic_review' or semantic_review.get('change')!=change
            or semantic_review.get('source_sha')!=head or semantic_review.get('target_sha')!=snapshot['target_sha']
            or semantic_review.get('scope_digest')!=report['scope_digest']
            or not set(report['review_paths']).issubset(semantic_review.get('reviewed_paths',[]))):
            raise ValueError('SEMANTIC_REVIEW_IDENTITY_OR_SCOPE')
        if semantic_review.get('status') not in ('compatible','requires_review','conflict_detected','undetermined'):
            raise ValueError('SEMANTIC_REVIEW_STATUS')
        for finding in semantic_review['findings']:
            if finding.get('type')=='functional' and not finding.get('references'):raise ValueError('SEMANTIC_EVIDENCE_REQUIRED')
            for ref in finding.get('references',[]):
                if ref['path'] not in report['review_paths']:raise ValueError('SEMANTIC_REFERENCE_OUTSIDE_SCOPE')
                if ref['revision'] not in (head,snapshot['target_sha']):raise ValueError('SEMANTIC_REFERENCE_REVISION')
                if ref.get('observation')=='worktree':
                    if ref['revision']!=head:raise ValueError('SEMANTIC_WORKTREE_REVISION')
                    payload=worktree_document(root,ref['path'],project,reference_budget)
                else:payload=blob(root,ref['revision'],ref['path'],project,reference_budget)
                if hashlib.sha256(payload).hexdigest()!=ref['sha256']:raise ValueError('SEMANTIC_REFERENCE_CHANGED')
        semantic_status=semantic_review['status'];report['findings']+=semantic_review['findings']
        if semantic_status=='compatible':
            report['findings']=[row for row in report['findings'] if row['reason']!='CONTRACT_OR_CONSUMER_REVIEW_REQUIRED']
            report['preserved_evidence'].append('Dependency impact reviewed against the exact source/target/scope; recommendations retained')
        report['dimensions']['contracts']='complete' if semantic_status in ('compatible','conflict_detected') and not semantic_review.get('limitations') else 'partial'
        report['limitations']+=semantic_review.get('limitations',[])
    complete=all(v=='complete' for v in report['dimensions'].values()) and not report['limitations']
    report['coverage']='complete' if complete else 'partial'
    if textual_conflict or semantic_status=='conflict_detected':report['outcome']='conflict_detected'
    elif semantic_status=='compatible' and complete and not report['findings'] and report['freshness']=='current':report['outcome']='compatible'
    elif report['findings'] or semantic_status=='requires_review' or (impact['known'] and semantic_status is None):report['outcome']='requires_review'
    report['actions']=['Reconciliar reglas/alcance con el responsable y revisar checks propuestos'] if report['outcome']!='compatible' else ['Continuar con gates y autorizaciones vigentes']
    if report['freshness']!='current':report['actions'].append('Obtener nuevo snapshot y recalcular compatibilidad; conservar pruebas locales intactas')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['inspect','simulate'],nargs='?');parser.add_argument('--describe-contracts',action='store_true')
    parser.add_argument('--repo',type=Path);parser.add_argument('--handoff');parser.add_argument('--target-snapshot')
    parser.add_argument('--simulation');parser.add_argument('--semantic-review');parser.add_argument('--current-target')
    parser.add_argument('--source-sha');parser.add_argument('--scratch',type=Path);parser.add_argument('--out')
    args=parser.parse_args()
    if args.describe_contracts:print(json.dumps(CONTRACTS));return 0
    try:
        root=args.repo.resolve();snapshot=read(safe_path(root,args.target_snapshot))
        if args.action=='simulate':value=simulate(root,args.source_sha,snapshot,args.scratch)
        else:
            project=read(safe_path(root,'docs/proyecto.json'));handoff=read(safe_path(root,args.handoff))
            from transiciones import validate_handoff
            validate_handoff(root,args.handoff)
            optional=lambda name:read(safe_path(root,name)) if name else None
            value=inspect(root,project,handoff,snapshot,optional(args.simulation),optional(args.semantic_review),optional(args.current_target))
            for argument,field in ((args.target_snapshot,'target_snapshot_ref'),(args.simulation,'simulation_ref'),
                                   (args.semantic_review,'semantic_review_ref'),(args.current_target,'current_target_ref')):
                if argument:value[field]={'path':argument,'sha256':file_hash(safe_path(root,argument))}
        schema='compatibilidad-simulation' if args.action=='simulate' else 'compatibilidad'
        validate_data(root,'docs/plantillas/'+schema+'.schema.json',value)
        if args.out:hu_export(root,args.out,value,snapshot['change'])
        print(json.dumps(value,ensure_ascii=False));return 0
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as exc:
        print(json.dumps({'outcome':'undetermined','error':str(exc) if isinstance(exc,ValueError) else type(exc).__name__}));return 4


if __name__=='__main__':raise SystemExit(main())
