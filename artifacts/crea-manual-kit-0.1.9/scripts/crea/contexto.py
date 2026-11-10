"""Seleccionar referencias e impacto local; no ejecuta suites, remoto o reparaciones.

API: inspect produce observaciones; logical congela obligaciones; review integra
la observaciÃ³n en el handoff; check contrasta polÃ­tica y reconciliaciÃ³n. Ver
scripts/crea/CONTEXTO.md para responsabilidades y ejemplos.
"""
import argparse
from fnmatch import fnmatchcase
import hashlib
import json
from pathlib import Path
import re
import time

DEPENDENCY_ERROR = None
try:
    from testing import git_adapter, schemas
    from testing.common import KIT, digest, read, safe_path, resolve_reference
except ImportError as exc:
    DEPENDENCY_ERROR = type(exc).__name__

class _Observation(dict):
    pass


CONDITIONS = ('CONTEXT_SOURCES_CURRENT', 'DOCUMENTATION_IMPACT_RECONCILED')


def consumer_impact(project, target_paths, story_paths):
    """Reuse the component graph; direct ownership differs from dependency closure."""
    config=project.get('context_management',{})
    if not config.get('enabled'):
        return {'known':False,'target_components':[],'story_components':[], 'affected_consumers':[],
                'shared_components':[],'unknown_paths':sorted(set(target_paths+story_paths))}
    validate_policy(project)
    rows=config['components']; reverse={row['id']:set() for row in rows}
    for row in rows:
        for dependency in row['dependencies']: reverse[dependency].add(row['id'])
    def mapped(paths):
        matches={};unknown=[]
        for name in paths:
            found={row['id'] for row in rows if any(fnmatchcase(name,p) for p in row['paths'])}
            if not found:unknown.append(name)
            matches[name]=found
        return set().union(*matches.values()) if matches else set(),unknown
    target,unknown_target=mapped(target_paths); story,unknown_story=mapped(story_paths)
    visited=set(); pending=list(target)
    while pending:
        key=pending.pop()
        if key in visited:continue
        visited.add(key);pending.extend(reverse[key])
    return {'known':True,'target_components':sorted(target),'story_components':sorted(story),
            'affected_consumers':sorted((visited-target)&story),'shared_components':sorted(target&story),
            'unknown_paths':sorted(set(unknown_target+unknown_story))}



def enabled(project):
    return project.get('context_management', {}).get('enabled', False)


def policy_digest(project):
    return digest({'context_management': project.get('context_management'),
                   'exclude_from_context': project['inventory']['exclude_from_context'],
                   'rules': project.get('rules')})


def validate_policy(project,root=None):
    if not enabled(project): return
    cm=project['context_management']
    ids=[x['id'] for x in cm['components']]
    if len(ids)!=len(set(ids)): raise ValueError('CONTEXT_DUPLICATE_COMPONENT')
    rules=[x['id'] for x in cm['impact_rules']]
    if len(rules)!=len(set(rules)): raise ValueError('CONTEXT_DUPLICATE_IMPACT_RULE')
    for component in cm['components']:
        if set(component['dependencies'])-set(ids): raise ValueError('CONTEXT_UNKNOWN_DEPENDENCY')
        if root is not None:
            for doc in component['documents']: safe_path(root,doc['path'])
    for rule in cm['impact_rules']:
        if set(rule['components'])-set(ids): raise ValueError('CONTEXT_UNKNOWN_IMPACT_COMPONENT')
        if not rule['components'] and not rule['paths']: raise ValueError('CONTEXT_IMPACT_SELECTOR_REQUIRED')
        if root is not None:
            for name in rule['documents']: safe_path(root,name)


def components_for(project, paths=(), explicit=()):
    validate_policy(project)
    catalog = {x['id']: x for x in project['context_management']['components']}
    if len(catalog) != len(project['context_management']['components']):
        raise ValueError('CONTEXT_DUPLICATE_COMPONENT')
    selected = set(explicit)
    unknown = []
    for path in paths:
        matched = {key for key, row in catalog.items() if any(fnmatchcase(path,p) for p in row['paths'])}
        selected.update(matched)
        if not matched:
            unknown.append(path)
    pending = sorted(selected)
    visited = set()
    while pending:
        key = pending.pop()
        if key in visited:
            continue
        if key not in catalog:
            raise ValueError('CONTEXT_UNKNOWN_COMPONENT: ' + key)
        visited.add(key)
        pending.extend(catalog[key]['dependencies'])
    return sorted(visited), sorted(set(unknown))


def logical(project, components, triggers=()):
    if not enabled(project):
        raise ValueError('CONTEXT_NOT_ADOPTED')
    selected, _ = components_for(project, explicit=components)
    catalog = {x['id']:x for x in project['context_management']['components']}
    documents = {}
    for key in selected:
        for doc in catalog[key]['documents']:
            name=doc['path']
            if name in documents and documents[name] != doc:
                raise ValueError('CONTEXT_DOCUMENT_MAPPING_CONFLICT')
            documents[name]=doc
    for rule in project['context_management']['impact_rules']:
        # Path-driven targets are frozen conservatively even before the future diff exists.
        if set(rule['components']) & set(selected) or rule['paths']:
            for name in rule['documents']:
                documents.setdefault(name, {'path':name,'kind':'technical',
                    'roles':['principal','planner','developer','tester','reviewer'],
                    'phases':['planificacion','implementacion','pruebas','revision','cierre','entrega']})
    return {'schema_version':'1.0','policy_digest':policy_digest(project),
            'components':selected,'triggers':sorted(set(triggers)),
            'documents':[documents[name] for name in sorted(documents)]}


def path_observation(root, base):
    """Git complet en chemins seulement: aucun contenu exclu n'est lu ici."""
    calls=0
    def git(*args):
        nonlocal calls
        calls += 1
        return git_adapter.git(root,*args)
    if Path(git('rev-parse','--show-toplevel').decode().strip()).resolve()!=Path(root).resolve():
        raise ValueError('NOT_REPOSITORY_ROOT')
    base_sha=git('rev-parse','--verify',base+'^{commit}').decode().strip()
    head=git('rev-parse','HEAD').decode().strip()
    git('merge-base','--is-ancestor',base_sha,head)
    layers={
        'head':git_adapter.parse_diff(git('diff','--no-ext-diff','--name-status','-z','-M',base_sha,'HEAD','--')),
        'staged':git_adapter.parse_diff(git('diff','--no-ext-diff','--cached','--name-status','-z','-M','--')),
        'unstaged':git_adapter.parse_diff(git('diff','--no-ext-diff','--name-status','-z','-M','--')),
        'untracked':[{'status':'A','path':p,'old_path':None} for p in git('ls-files','--others','--exclude-standard','-z').decode('utf-8').split('\0') if p],
        'conflicts':[{'status':'U','path':p,'old_path':None} for p in git('diff','--name-only','--diff-filter=U','-z','--').decode('utf-8').split('\0') if p]}
    paths=sorted({p for rows in layers.values() for row in rows for p in (row['path'],row['old_path']) if p})
    value={'schema_version':'1.0','base_sha':base_sha,'head_sha':head,'layers':layers,'paths':paths}
    value['identity']=digest(value)
    return value,calls


def excluded(project,name):
    for pattern in project['inventory']['exclude_from_context']:
        if (pattern.endswith('/') and (name==pattern.rstrip('/') or name.startswith(pattern))) or fnmatchcase(name,pattern):
            return True
    return False


def reference_map(project,selected,observation,role,phase,triggers=()):
    catalog={x['id']:x for x in project['context_management']['components']}
    sources={}
    for key in selected:
        for doc in catalog[key]['documents']:
            if role in doc['roles'] and phase in doc['phases']:
                row=sources.setdefault(doc['path'],{'path':doc['path'],'kind':doc['kind'],'reasons':[]})
                row['reasons'].append('component:'+key)
    for rule in project['context_management']['impact_rules']:
        applicable=set(rule['components']) & set(selected) or any(fnmatchcase(p,pat) for p in observation['paths'] for pat in rule['paths'])
        if applicable and set(rule['triggers']) & (set(triggers) | ({'path_change'} if observation['paths'] else set())):
            for name in rule['documents']:
                sources.setdefault(name,{'path':name,'kind':'technical','reasons':['impact:'+rule['id']]})
    return sources


def target_for(row):
    if row['operation']=='move':
        if not row.get('target_path') or row['target_path']==row['path']:
            raise ValueError('CONTEXT_MOVE_TARGET_REQUIRED')
        return row['target_path']
    if 'target_path' in row:
        raise ValueError('CONTEXT_TARGET_ONLY_FOR_MOVE')
    return row['path']


def move_is_bound(row,observation,moves):
    target=target_for(row)
    observed=any(r['status']=='R' and r['old_path']==row['path'] and r['path']==target
                 for rows in observation['layers'].values() for r in rows)
    declared=any(m['from']==row['path'] and m['to']==target and any(r['path']==target and r.get('sha256')==m['sha256'] for r in row['references']) for m in moves)
    return observed or declared


def inspect(root,project,change,role,phase,base,components=(),triggers=(),history=(),rule_context=None,dispositions=(),moves=()):
    started=time.perf_counter()
    observation,processes=path_observation(root,base)
    semantic={'components':[],'sources':[],'rules':[],'impact':[],'unknown_paths':[],
              'omitted':[],'pending':[],'partial':False,'not_performed':['semantic_review','suites','remote']}
    metrics={'files_read':0,'bytes_read':0,'git_processes':processes,'suite_processes':0,'remote_processes':0}
    if not enabled(project):
        return _Observation({'kind':'context_observation','schema_version':'1.0','change':change,'role':role,'phase':phase,
                'policy_digest':None,'semantic':semantic,'observation':observation,'metrics':metrics})
    selected,unknown=components_for(project,observation['paths'],components)
    semantic['components'],semantic['unknown_paths']=selected,unknown
    semantic['pending']=[{'path':name,'owner':'planner','action':'review_component_mapping','reason':'unmapped_changed_path'} for name in unknown]
    sources=reference_map(project,selected,observation,role,phase,triggers)
    for name in history:
        sources.setdefault(name,{'path':name,'kind':'history','reasons':['explicit_history']})
    limits=project['context_management']['limits']
    cache={}
    dispositions={row['path']:row for row in dispositions}
    deleted={row['path'] for rows in observation['layers'].values() for row in rows if row['status']=='D'}
    def load(name):
        if name in cache: return cache[name]
        reason=None
        try:
            path=safe_path(root,name)
        except (ValueError,OSError):
            path=None; reason='unsafe_path'
        if reason is None and excluded(project,name): reason='excluded'
        if reason is None and (name.startswith('openspec/changes/archive/') or name.startswith('docs/hu/') and not name.startswith('docs/hu/'+change+'/')) and name not in history:
            reason='history_not_explicit'
        if reason is None and not path.is_file():
            disposition=dispositions.get(name,{})
            if disposition.get('operation')=='delete' and disposition.get('status')=='updated' and name in deleted:
                semantic['omitted'].append({'path':name,'reason':'declared_deletion_observed'})
                raise ValueError('CONTEXT_DECLARED_ABSENCE')
            if disposition.get('operation')=='move' and disposition.get('target_path'):
                target=disposition['target_path']
                try:
                    path=safe_path(root,target)
                    if excluded(project,target): reason='excluded'
                    elif (target.startswith('openspec/changes/archive/') or target.startswith('docs/hu/') and not target.startswith('docs/hu/'+change+'/')) and target not in history:
                        reason='history_not_explicit'
                    elif not move_is_bound(disposition,observation,moves): reason='move_not_bound'
                    elif not path.is_file(): reason='missing'
                except (ValueError,OSError): reason='unsafe_path'
            else: reason='missing'
        if reason is None and (path.stat().st_size>limits['per_document_bytes'] or metrics['bytes_read']+path.stat().st_size>limits['total_bytes']): reason='byte_limit'
        if reason:
            semantic['omitted'].append({'path':name,'reason':reason}); semantic['partial']=True
            raise ValueError('CONTEXT_SOURCE_UNAVAILABLE')
        with path.open('rb') as stream:
            payload=stream.read(min(limits['per_document_bytes'],limits['total_bytes']-metrics['bytes_read'])+1)
        metrics['files_read']+=1; metrics['bytes_read']+=len(payload)
        if len(payload)>limits['per_document_bytes'] or metrics['bytes_read']>limits['total_bytes']:
            semantic['omitted'].append({'path':name,'reason':'byte_limit'}); semantic['partial']=True
            raise ValueError('CONTEXT_SOURCE_UNAVAILABLE')
        disposition=dispositions.get(name,{})
        if disposition.get('operation')=='move':
            expected=next((r.get('sha256') for r in disposition['references'] if r['path']==disposition.get('target_path')),None)
            if not expected or hashlib.sha256(payload).hexdigest()!=expected:
                semantic['omitted'].append({'path':name,'reason':'move_content_changed'}); semantic['partial']=True
                raise ValueError('CONTEXT_MOVE_CONTENT_CHANGED')
        cache[name]=payload
        return payload
    if rule_context is not None:
        from transiciones import select_rules
        try:
            semantic['rules']=select_rules(root,project,rule_context['layers'],rule_context['capabilities'],rule_context['not_applicable_reason'],reader=load)
            for row in semantic['rules']:
                sources.setdefault(row['path'],{'path':row['path'],'kind':'rule','reasons':['normative_selection']})
        except ValueError:
            semantic['partial']=True
    for name,row in sorted(sources.items()):
        try: payload=load(name)
        except ValueError: continue
        semantic['sources'].append({**row,'reasons':sorted(set(row['reasons'])),'phase':phase,'exists':True,'observed_sha256':hashlib.sha256(payload).hexdigest()})
    trigger_set=set(triggers)
    if observation['paths']: trigger_set.add('path_change')
    for rule in sorted(project['context_management']['impact_rules'],key=lambda r:r['id']):
        applicable=(bool(set(rule['components'])&set(selected)) or any(fnmatchcase(p,pat) for p in observation['paths'] for pat in rule['paths']))
        if applicable and set(rule['triggers'])&trigger_set:
            for name in rule['documents']:
                semantic['impact'].append({'path':name,'rule':rule['id'],'reason':rule['reason'],'owner':rule['owner']})
    semantic['impact']=sorted({(r['path'],r['rule']):r for r in semantic['impact']}.values(),key=lambda r:(r['path'],r['rule']))
    metrics['duration_seconds']=round(time.perf_counter()-started,6)
    return _Observation({'kind':'context_observation','schema_version':'1.0','change':change,'role':role,'phase':phase,
            'policy_digest':policy_digest(project),'semantic':semantic,'observation':observation,'metrics':metrics})


def review(observation,stage,documents,null_reason=None):
    return {'schema_version':'1.0','stage':stage,'role':observation['role'],'phase':observation['phase'],'git_observation':observation['observation'],
            'sources':observation['semantic']['sources'],'documents':documents,'null_reason':null_reason}


def validate_logical(project,management):
    if management != logical(project,management['components'],management['triggers']):
        raise ValueError('CONTEXT_LOGICAL_POLICY_CHANGED')


def validate_metadata(root,project,h):
    management=h['context']['management']
    validate_logical(project,management)
    evidence=h['evidence'].get('context_review')
    if evidence is None: return
    obs=evidence['git_observation']
    if obs['identity']!=digest({k:v for k,v in obs.items() if k!='identity'}):
        raise ValueError('CONTEXT_GIT_OBSERVATION_INVALID')
    names=sorted({p for rows in obs['layers'].values() for row in rows for p in (row['path'],row['old_path']) if p})
    if names!=obs['paths']: raise ValueError('CONTEXT_GIT_PATHS_INVALID')
    allowed={d['path'] for d in management['documents']} | {r['path'] for r in h['context']['rules']}
    allowed.update(p for r in project['context_management']['impact_rules'] for p in r['documents'])
    for source in evidence['sources']:
        if source['path'] not in allowed or excluded(project,source['path']):
            raise ValueError('CONTEXT_SOURCE_OUTSIDE_SELECTION')
        safe_path(root,source['path'])
    rules={r['id']:r for r in project['context_management']['impact_rules']}
    for row in evidence['documents']:
        rule=rules.get(row['rule'])
        if not rule or row['path'] not in rule['documents'] or row['owner']!=rule['owner'] or row['reason']!=rule['reason']:
            raise ValueError('CONTEXT_DOCUMENT_ROW_INVALID')
        target=target_for(row)
        if row['operation']=='move' and not move_is_bound(row,obs,h['scope']['moves']):
            raise ValueError('CONTEXT_MOVE_NOT_BOUND')
        if row['status']=='updated':
            if row['operation']=='delete':
                deleted={r['path'] for rows in obs['layers'].values() for r in rows if r['status']=='D'}
                if row['path'] not in deleted or safe_path(root,row['path']).exists():
                    raise ValueError('CONTEXT_DELETION_NOT_OBSERVED')
            elif not any(r['path']==row.get('target_path',row['path']) and r.get('sha256') for r in row['references']):
                raise ValueError('CONTEXT_UPDATED_TARGET_REFERENCE_REQUIRED')
        for ref in row['references']:
            safe_path(root,ref['path'])
            if excluded(project,ref['path']) or ref['path']!=target or not ref.get('sha256'):
                raise ValueError('CONTEXT_DOCUMENT_REFERENCE_OUTSIDE_TARGET')


def normalized_git(root,h,observation):
    projection={'version':'content-v2','change':h['identity']['change'],
                'context':git_adapter.handoff_context(h),'history':{},'moves':h['scope']['moves'],
                'sync':h['scope']['sync'],'git_inputs':h['scope']['git_inputs']}
    metadata=set()
    for name in observation['paths']:
        if git_adapter.managed(root,name,projection): metadata.add(name)
    layers={key:[row for row in rows if not all(p in metadata for p in (row['path'],row['old_path']) if p)]
            for key,rows in observation['layers'].items()}
    return {'base_sha':observation['base_sha'],'head_sha':observation['head_sha'],'layers':layers}


def check(root,project,h,observation=None):
    settings=project['workflow'].get('transitions',{'mode':'informative','blocking_conditions':[]})
    result={'check_status':'completed','new_control_effect':'allow','findings':[],'exit_code':0}
    if not enabled(project): return result
    def finding(condition,reason):
        result['findings'].append({'condition_id':condition,'reason':reason,'class':'blocking_noncompliance'})
    management=h['context'].get('management')
    if not management:
        finding(CONDITIONS[0],'CONTEXT_LOGICAL_SELECTION_MISSING')
    else:
        try: validate_logical(project,management)
        except ValueError as exc: finding(CONDITIONS[0],str(exc))
    if observation is None:
        raise ValueError('CONTEXT_CURRENT_OBSERVATION_REQUIRED')
    if not isinstance(observation,_Observation):
        raise ValueError('CONTEXT_INTERNAL_OBSERVATION_REQUIRED')
    if observation['change']!=h['identity']['change'] or observation['policy_digest']!=policy_digest(project):
        raise ValueError('CONTEXT_OBSERVATION_IDENTITY_MISMATCH')
    if observation['semantic']['partial']:
        finding(CONDITIONS[0],'CONTEXT_READING_PARTIAL')
    if management and set(observation['semantic']['components'])-set(management['components']):
        finding(CONDITIONS[1],'CONTEXT_UNEXPECTED_COMPONENT_RECONCILE_SCOPE')
    evidence=h['evidence'].get('context_review')
    if not evidence:
        finding(CONDITIONS[1],'CONTEXT_REVIEW_MISSING')
    else:
        # The initial hashes are historical observations, never current file refs.
        final_required=h['continuation']['transition'] in ('to_test','to_review','to_sync','to_archive','to_publish','to_pr')
        if final_required and evidence['stage']!='final': finding(CONDITIONS[1],'FINAL_CONTEXT_REVIEW_REQUIRED')
        if evidence['stage']=='final':
            expected={(x['path'],x['rule']):x for x in observation['semantic']['impact']}
            rows={(x['path'],x['rule']):x for x in evidence['documents']}
            if len(rows)!=len(evidence['documents']): finding(CONDITIONS[1],'DUPLICATE_CONTEXT_REVIEW_ROW')
            if not expected and not rows and not (evidence['null_reason'] or '').strip():
                finding(CONDITIONS[1],'FINAL_NULL_IMPACT_REASON_REQUIRED')
            if set(expected)-set(rows): finding(CONDITIONS[1],'DOCUMENTATION_IMPACT_ROWS_MISSING')
            current={x['path']:x['observed_sha256'] for x in observation['semantic']['sources']}
            previous={x['path']:x['observed_sha256'] for x in evidence['sources']}
            if normalized_git(root,h,evidence['git_observation']) != normalized_git(root,h,observation['observation']):
                finding(CONDITIONS[0],'CONTEXT_GIT_OBSERVATION_STALE')
            if management:
                expected_sources=set(reference_map(project,management['components'],evidence['git_observation'],evidence['role'],evidence['phase'],management['triggers']))
                expected_sources.update(r['path'] for r in h['context']['rules'])
                deleted_review={r['path'] for r in evidence['documents'] if r['operation']=='delete' and r['status']=='updated'}
                if expected_sources-deleted_review != set(previous):
                    finding(CONDITIONS[0],'CONTEXT_SOURCE_OBSERVATIONS_INCOMPLETE')
            if any(current[path]!=previous[path] for path in current.keys() & previous.keys()): finding(CONDITIONS[0],'CONTEXT_SOURCE_OBSERVATIONS_STALE')
            for key,row in rows.items():
                if key not in expected or any(row[k]!=expected[key][k] for k in ('owner','reason')):
                    finding(CONDITIONS[1],'DOCUMENTATION_ROW_POLICY_MISMATCH')
                if row['status']=='pending' or not row['justification'].strip(): finding(CONDITIONS[1],'DOCUMENTATION_IMPACT_PENDING')
                try:
                    target=target_for(row)
                    if row['operation']=='move' and not move_is_bound(row,observation['observation'],h['scope']['moves']):
                        raise ValueError('CONTEXT_MOVE_NOT_BOUND')
                    if row['status']=='updated':
                        if row['operation']=='delete':
                            deleted={x['path'] for rows in observation['observation']['layers'].values() for x in rows if x['status']=='D'}
                            if row['path'] not in deleted or safe_path(root,row['path']).exists(): raise ValueError('DOCUMENTATION_DELETION_NOT_OBSERVED')
                        elif not any(ref['path']==target and ref.get('sha256') for ref in row['references']): raise ValueError('DOCUMENTATION_UPDATE_REFERENCE_REQUIRED')
                    for ref in row['references']:
                        safe_path(root,ref['path'])
                        if excluded(project,ref['path']) or ref['path']!=target or not ref.get('sha256'):
                            raise ValueError('DOCUMENTATION_REFERENCE_OUTSIDE_TARGET')
                        # All target content was read with the same selection limits. No second unbounded resolver.
                        actual=current.get(row['path']) if row['operation']=='move' else current.get(target)
                        if not actual or actual!=ref['sha256']: raise ValueError('DOCUMENTATION_REFERENCE_UNAVAILABLE')
                except (ValueError,OSError) as exc:
                    finding(CONDITIONS[0],str(exc) if isinstance(exc,ValueError) else 'DOCUMENTATION_REFERENCE_UNAVAILABLE')
        elif not evidence['documents'] and not (evidence['null_reason'] or '').strip():
            finding(CONDITIONS[1],'PLANNED_IMPACT_OR_NULL_REASON_REQUIRED')
    blocking=settings['mode']=='enforcing' and any(f['condition_id'] in settings['blocking_conditions'] for f in result['findings'])
    result['exit_code']=2 if blocking else 0
    result['new_control_effect']='block' if blocking else 'report_only' if result['findings'] else 'allow'
    return result


def save(root,name,value,change):
    if not re.fullmatch(r'docs/hu/'+re.escape(change)+r'/contexto/(planificacion|implementacion|pruebas|revision|cierre|entrega)-[1-9][0-9]*\.json',name):
        raise ValueError('CONTEXT_OUTPUT_OUTSIDE_CASE')
    path=safe_path(root,name)
    if path.exists(): raise ValueError('CONTEXT_OUTPUT_ALREADY_EXISTS')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    # Auxiliary reports remain functional files. No path-based metadata exclusion.


def main(argv=None):
    if DEPENDENCY_ERROR:
        print(json.dumps({'check_status':'validator_error','reason':'DEPENDENCY_UNAVAILABLE','exit_code':4})); return 4
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['select','impact','check'])
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--change',required=True)
    parser.add_argument('--base',default='HEAD')
    parser.add_argument('--role',choices=['principal','planner','developer','tester','reviewer'],required=True)
    parser.add_argument('--phase',choices=['planificacion','implementacion','pruebas','revision','cierre','entrega'],required=True)
    parser.add_argument('--component',action='append',default=[])
    parser.add_argument('--trigger',action='append',default=[])
    parser.add_argument('--history',action='append',default=[])
    parser.add_argument('--handoff')
    parser.add_argument('--out')
    args=parser.parse_args(argv)
    try:
        if not re.fullmatch(r'[a-zA-Z0-9_-]+',args.change): raise ValueError('CONTEXT_CHANGE_INVALID')
        project=schemas.validate('project',read(safe_path(args.repo,'docs/proyecto.json')))
        h=None
        if args.handoff:
            from transiciones import validate_handoff
            h=validate_handoff(args.repo,args.handoff)
            if (h['identity']['change'],h['identity']['phase'],h['identity']['sender'])!=(args.change,args.phase,args.role):
                raise ValueError('CONTEXT_HANDOFF_IDENTITY_MISMATCH')
        cm=h['context'].get('management',{}) if h else {}
        value=inspect(args.repo,project,args.change,args.role,args.phase,args.base,
                      args.component or cm.get('components',[]),args.trigger or cm.get('triggers',[]),args.history, h['context'] if h else None, h['evidence'].get('context_review',{}).get('documents',[]) if h else [], h['scope']['moves'] if h else [])
        code=0
        if args.action=='check':
            if h is None: raise ValueError('CONTEXT_HANDOFF_REQUIRED')
            report=check(args.repo,project,h,value); value['check']=report; code=report['exit_code']
        if args.out: save(args.repo,args.out,value,args.change)
        print(json.dumps(value,ensure_ascii=False,indent=2)); return code
    except (ValueError,OSError,KeyError,TypeError,ImportError) as exc:
        print(json.dumps({'check_status':'validator_error','reason':str(exc) if isinstance(exc,ValueError) else type(exc).__name__,'exit_code':4})); return 4

if __name__=='__main__': raise SystemExit(main())
