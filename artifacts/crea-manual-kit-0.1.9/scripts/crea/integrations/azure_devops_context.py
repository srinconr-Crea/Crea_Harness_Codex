"""Bounded Azure CLI context reader. Remote content is data, never executable input."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

API_DOCUMENTED = '7.1-preview.4'
# invoke 1.0.9 parses float(version.replace('-preview', '')); suffix .4 fails.
# The documented version grammar permits stage without resource revision.
API_CLI = '7.1-preview'
COMMENTS_RESOURCE = 'comments'
PAIRS = {'planificacion': 'planner', 'revision': 'reviewer'}
REQUEST_FIELDS = {'schema_version','request_id','hu_id','change','attempt','phase','executor_role','created_by','created_at_utc','work_item_id','organization','project_id','project_name','evidence_dir','previous_snapshot_ref'}


class InvalidInput(ValueError):
    pass


class QueryFailure(Exception):
    pass


def now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


def load(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as exc:
        raise InvalidInput('JSON input unavailable or invalid') from exc


def positive(value):
    return type(value) is int and value > 0


def safe_path(root, relative):
    if not isinstance(relative, str) or '\\' in relative or ':' in relative:
        raise InvalidInput('Expected relative portable path')
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts:
        raise InvalidInput('Path outside HU expediente')
    candidate = root / p
    for parent in [candidate, *candidate.parents]:
        if parent == root.parent:
            break
        if parent.is_symlink() or (hasattr(parent, 'is_junction') and parent.is_junction()):
            raise InvalidInput('Links and junctions are not permitted')
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise InvalidInput('Path outside project')
    return candidate


def valid_org(value):
    if not isinstance(value, str):
        return False
    u = urlsplit(value)
    return (u.scheme == 'https' and not u.username and not u.password and not u.query and not u.fragment and
            ((u.hostname == 'dev.azure.com' and re.fullmatch(r'/[A-Za-z0-9_.-]+/?', u.path)) or
             (u.hostname and re.fullmatch(r'[A-Za-z0-9-]+\.visualstudio\.com', u.hostname) and u.path in ('','/'))))


def validate(config_path, request_path, out=None):
    config_path, request_path = Path(config_path).absolute(), Path(request_path).absolute()
    root = config_path.parent.parent
    if config_path != root / 'docs/proyecto.json':
        raise InvalidInput('Config must be docs/proyecto.json in selected project')
    config = load(config_path)
    if not isinstance(config,dict) or not isinstance(config.get('integrations',{}),dict):
        raise InvalidInput('Invalid integration config')
    cfg = config.get('integrations', {}).get('azure_devops_context', {})
    if not isinstance(cfg,dict):
        raise InvalidInput('Invalid Azure context config')
    if cfg.get('enabled') is not True:
        raise InvalidInput('Azure context integration disabled')
    cfg = {'timeout_seconds':30,'max_comment_pages':100,'comments_page_size':100, **cfg}
    if not valid_org(cfg.get('organization')):
        raise InvalidInput('Organization must be an HTTPS Azure DevOps organization without credentials')
    for key, maximum in [('timeout_seconds',600),('max_comment_pages',1000),('comments_page_size',200)]:
        if not positive(cfg[key]) or cfg[key] > maximum:
            raise InvalidInput('Invalid bounded limit: ' + key)
    req = load(request_path)
    if not isinstance(req,dict) or set(req) != REQUEST_FIELDS:
        raise InvalidInput('Unexpected or missing request fields')
    if type(req['schema_version']) is not int or req['schema_version'] != 1 or req['created_by'] != 'principal' or not isinstance(req['phase'],str) or PAIRS.get(req['phase']) != req['executor_role']:
        raise InvalidInput('Only principal-prepared Planner/Reviewer phase requests are permitted')
    if not positive(req['attempt']) or not positive(req['work_item_id']):
        raise InvalidInput('Attempt and work item must be positive integers')
    for key in ['change','hu_id','request_id']:
        if not isinstance(req[key],str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', req[key]):
            raise InvalidInput('Invalid identity: ' + key)
    try:
        created = datetime.fromisoformat(req['created_at_utc'].replace('Z','+00:00'))
        if created.utcoffset().total_seconds() != 0:
            raise ValueError()
    except (ValueError,TypeError,AttributeError):
        raise InvalidInput('Expected UTC created_at_utc')
    for key in ['organization','project_id','project_name']:
        value = cfg.get(key)
        if not isinstance(value,str) or not value.strip() or req[key] != value or any(c in value for c in '\r\n'):
            raise InvalidInput('Destination missing or inconsistent: ' + key)
    if not re.fullmatch(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', cfg['project_id']):
        raise InvalidInput('Expected canonical project UUID')
    prefix = f'docs/hu/{req["change"]}'
    expected_request = f'{prefix}/inputs/azure-devops/{req["phase"]}-{req["attempt"]}.json'
    if safe_path(root, expected_request) != request_path:
        raise InvalidInput('Request path does not match HU/phase/attempt')
    expected_evidence = f'{prefix}/evidence/azure-devops/{req["phase"]}-{req["attempt"]}'
    if req['evidence_dir'] != expected_evidence:
        raise InvalidInput('Evidence path does not match HU/phase/attempt')
    evidence = safe_path(root, expected_evidence)
    previous = None
    if req['phase'] == 'revision' and not req['previous_snapshot_ref']:
        raise InvalidInput('Reviewer requires Planner snapshot reference')
    if req['previous_snapshot_ref'] is not None:
        previous_path = safe_path(root, req['previous_snapshot_ref'])
        planner_base = root / prefix / 'evidence/azure-devops'
        if previous_path.parent.parent != planner_base or not previous_path.parent.name.startswith('planificacion-') or previous_path.name != 'snapshot.json':
            raise InvalidInput('Previous snapshot must belong to Planner in same HU')
        previous = load(previous_path)
        for key in ['hu_id','work_item_id','organization','project_id','project_name']:
            if previous.get(key) != req[key]:
                raise InvalidInput('Snapshot identity inconsistent with HU request')
    # One immutable work item identity per HU, including retries and phases.
    request_dir = root / prefix / 'inputs/azure-devops'
    for old_path in sorted(request_dir.glob('*.json')):
        if old_path == request_path:
            continue
        old = load(safe_path(root, old_path.relative_to(root).as_posix()))
        if old.get('hu_id') != req['hu_id'] or old.get('work_item_id') != req['work_item_id']:
            raise InvalidInput('HU already bound to another work item identity')
    if out is not None:
        out = Path(out).absolute()
        if out.parent != evidence or out.name == 'snapshot.json':
            raise InvalidInput('--out must be a new receipt in the exact evidence directory')
        safe_path(root, out.relative_to(root).as_posix())
        if out.exists() or (evidence / 'snapshot.json').exists():
            raise InvalidInput('Evidence already exists; use a new attempt')
    return root, cfg, req, evidence, previous


def item_argv(req):
    return ['az','boards','work-item','show','--id',str(req['work_item_id']),'--organization',req['organization'],'--detect','false','--expand','all','--output','json']


def comments_argv(req, cfg, token=None):
    argv = ['az','devops','invoke','--organization',req['organization'],'--detect','false','--area','wit','--resource',COMMENTS_RESOURCE,'--http-method','GET','--api-version',API_CLI,'--route-parameters','project='+req['project_id'],'workItemId='+str(req['work_item_id']),'--query-parameters','$top='+str(cfg['comments_page_size']),'includeDeleted=false','order=asc']
    if token:
        argv.append('continuationToken='+token)
    return argv + ['--output','json']


def cli_argv(argv):
    executable = shutil.which('az')
    if not executable:
        raise QueryFailure('cli_unavailable')
    if os.name == 'nt' and Path(executable).suffix.lower() in ('.cmd','.bat'):
        # Official Windows CLI layout: wbin/az.cmd -> ../python.exe -IBm azure.cli.
        # Never hand remote continuation tokens to a batch interpreter.
        python = Path(executable).parent.parent / 'python.exe'
        if not python.is_file():
            raise QueryFailure('windows_cli_python_unavailable')
        return [str(python),'-IBm','azure.cli',*argv[1:]]
    return [executable,*argv[1:]]


def transport(argv, timeout):
    env = dict(os.environ)
    env.update(AZURE_EXTENSION_USE_DYNAMIC_INSTALL='no', AZURE_CORE_COLLECT_TELEMETRY='no', AZURE_CORE_ONLY_SHOW_ERRORS='true')
    try:
        result = subprocess.run(cli_argv(argv), capture_output=True, text=True, encoding='utf-8', timeout=timeout, shell=False, env=env)
        if result.returncode:
            if '403' in result.stderr or 'Forbidden' in result.stderr:
                raise QueryFailure('forbidden')
            raise QueryFailure('cli_failed')
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired as exc:
        raise QueryFailure('timeout') from exc
    except (OSError, ValueError) as exc:
        raise QueryFailure('cli_unavailable_or_invalid_json') from exc


CLI_TRANSPORT = transport


def local_versions(timeout):
    try:
        versions = CLI_TRANSPORT(['az','version','--output','json'],timeout)
        core = versions.get('azure-cli')
        extension = versions.get('extensions',{}).get('azure-devops')
        return {'azure_cli':core or 'unknown','azure_devops':extension or 'unknown','status':'observed' if core and extension else 'incomplete','reason':None if core and extension else 'version_or_extension_missing'}
    except (QueryFailure,ValueError,TypeError,AttributeError):
        return {'azure_cli':'unknown','azure_devops':'unknown','status':'unknown','reason':'local_version_probe_failed'}


def sanitize(value):
    if isinstance(value,str):
        value = re.sub(r'(?i)\b(?:[A-Z0-9._%+-]+)@[A-Z0-9.-]+\.[A-Z]{2,}\b','[REDACTED_EMAIL]',value)
        value = re.sub(r'(?i)\b(?:bearer\s+\S+|(?:access_token|refresh_token|client_secret|token|password|secret|pat|authorization|sig)\s*[:=]\s*[^\s<]+)', '[REDACTED_SECRET]',value)
        value = re.sub(r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b','[REDACTED_JWT]',value)
        value = re.sub(r'https://[^/@\s]+:[^/@\s]+@', 'https://[REDACTED]@', value)
        value = re.sub(r'\b[A-Za-z0-9]{52}\b|\b[A-Za-z0-9]{75}AZDO[A-Za-z0-9]{5}\b','[REDACTED_PAT]',value)
        return value
    if isinstance(value,list):
        return [sanitize(v) for v in value]
    if isinstance(value,dict):
        return {k:sanitize(v) for k,v in value.items()}
    return value


def normalize_item(item, req):
    if not isinstance(item,dict) or item.get('id') != req['work_item_id'] or not positive(item.get('rev')):
        raise QueryFailure('work_item_identity_or_revision_invalid')
    fields = item.get('fields',{})
    if not isinstance(fields,dict) or fields.get('System.TeamProject') != req['project_name']:
        raise QueryFailure('project_mismatch_or_unverifiable')
    url = item.get('url')
    if not isinstance(url,str) or not url.startswith(req['organization'].rstrip('/') + '/'):
        raise QueryFailure('organization_mismatch_or_unverifiable')
    values = [fields.get(key,'') for key in ['System.Title','System.Description','Microsoft.VSTS.Common.AcceptanceCriteria']]
    if not all(isinstance(v,str) for v in values):
        raise QueryFailure('work_item_fields_invalid')
    links = []
    relations = item.get('relations',[])
    if not isinstance(relations,list):
        raise QueryFailure('work_item_relations_invalid')
    for relation in relations:
        if not isinstance(relation,dict) or not isinstance(relation.get('url'),str) or not isinstance(relation.get('rel'),str):
            raise QueryFailure('work_item_relation_invalid')
        links.append({'rel':relation['rel'], 'url':relation['url']})
    return dict(title=values[0],description=values[1],acceptance_criteria=values[2],rev=item['rev'],links=links)


def read_comments(req, cfg, call):
    confirmed, tokens, errors = {}, set(), []
    token, count, total = None, 0, None
    coverage = 'failed'
    for _ in range(cfg['max_comment_pages']):
        try:
            page = call(comments_argv(req,cfg,token), cfg['timeout_seconds'])
            if not isinstance(page,dict) or not isinstance(page.get('comments'),list) or type(page.get('count')) is not int or page['count'] != len(page['comments']):
                raise QueryFailure('comments_page_invalid')
            current_total = page.get('totalCount')
            if current_total is not None and (type(current_total) is not int or current_total < page['count']):
                raise QueryFailure('comments_total_invalid')
            if total is not None and current_total is not None and total != current_total:
                errors.append('comments_total_changed')
            total = current_total if total is None else total
            normalized = []
            for c in page['comments']:
                cid = c.get('id',c.get('commentId')) if isinstance(c,dict) else None
                if not positive(cid) or not positive(c.get('version')) or c.get('workItemId',req['work_item_id']) != req['work_item_id'] or not isinstance(c.get('text'),str) or c.get('isDeleted',False):
                    raise QueryFailure('comment_identity_or_format_invalid')
                normalized.append({k:v for k,v in dict(id=cid,version=c['version'],text=c['text'],created_at_utc=c.get('createdDate'),modified_at_utc=c.get('modifiedDate')).items() if v is not None})
            # Commit a page only after every entry has validated.
            for c in normalized:
                key = (c['id'],c['version'])
                if key in confirmed and confirmed[key] != c:
                    errors.append('comment_duplicate_conflict')
                elif key not in confirmed:
                    confirmed[key] = c
            count += 1
            body_token, header_token = page.get('continuationToken'), page.get('continuation_token')
            if body_token and header_token and body_token != header_token:
                errors.append('continuation_token_conflict')
                break
            token = body_token or header_token
            if token is not None and (not isinstance(token,str) or not token or len(token)>8192 or any(c in token for c in '\r\n')):
                raise QueryFailure('continuation_token_invalid')
            if not token:
                if page.get('nextPage') or (total is not None and len({k[0] for k in confirmed}) != total):
                    errors.append('pagination_inconsistent')
                coverage = 'complete' if confirmed else 'empty'
                break
            if token in tokens or not normalized:
                errors.append('continuation_repeated_or_empty_page')
                break
            tokens.add(token)
        except (QueryFailure,TimeoutError,PermissionError,ValueError,TypeError,KeyError) as exc:
            errors.append(str(exc) if isinstance(exc,QueryFailure) else 'comments_query_failed')
            break
    else:
        errors.append('max_comment_pages_reached')
    if errors:
        coverage = 'partial' if count else 'failed'
    return sorted(confirmed.values(),key=lambda c:(c['id'],c['version'])), coverage, count, errors


def compare(previous, current):
    fields = [key for key in ['title','description','acceptance_criteria'] if previous.get(key) != current.get(key)]
    old = {(c['id'],c['version']):c for c in previous.get('comments',[])}
    new = {(c['id'],c['version']):c for c in current.get('comments',[])}
    changed = [c for key,c in new.items() if old.get(key) != c]
    removed = [key for key in old if key not in new]
    # Conservative signal, never pretend automatic semantic classification is proof.
    decision = any(re.search(r'(?i)\b(decisi[oó]n|criteri[oa]|acceptance|requirement|requisito|must|debe|aprobad[oa])\b',c['text']) for c in changed)
    uncertain = bool(removed) or any(key in old and old[key] != c for key,c in new.items())
    return {'fields_changed':fields,'comments_changed':digest(previous.get('comments',[])) != digest(current.get('comments',[])), 'new_or_changed_comment_ids':[c['id'] for c in changed], 'removed_comment_ids':[k[0] for k in removed], 'requires_reconciliation':bool(fields or decision or uncertain), 'classification':'material_or_requires_human_review' if fields or decision or uncertain else ('informative_new_comments_review_required' if changed else 'unchanged'), 'semantic_classification':'heuristic_review_required'}


def exclusive(path, value):
    with open(path,'xb') as stream:
        stream.write(encode(value))


def execute(operation, config_path, request_path, out=None, transport=transport, version_probe=None):
    if operation not in ('preview','read') or (operation=='read' and out is None) or (operation=='preview' and out is not None):
        raise InvalidInput('Expected preview without --out or read with --out')
    root,cfg,req,evidence,previous = validate(config_path,request_path,out)
    base = dict(schema_version=1,hu=req['hu_id'],attempt=req['attempt'],role=req['executor_role'],operation='work_item_context_read',organization=req['organization'],project_id=req['project_id'],project_name=req['project_name'],work_item_id=req['work_item_id'],request_ref=Path(request_path).absolute().relative_to(root).as_posix(),request_sha256=hashlib.sha256(Path(request_path).read_bytes()).hexdigest())
    if operation == 'preview':
        return {**base,'status':'preview','work_item_argv':item_argv(req),'comments_argv':comments_argv(req,cfg),'api_documented':API_DOCUMENTED,'api_cli_requested':API_CLI,'comments_resource':COMMENTS_RESOURCE,'credential_check':'not_run','remote_read':'not_run'},0
    if version_probe is None:
        version_probe = local_versions if transport is CLI_TRANSPORT else lambda _: {'azure_cli':'unknown','azure_devops':'unknown','status':'synthetic_transport','reason':'test_double_no_local_cli_probe'}
    versions = version_probe(cfg['timeout_seconds'])
    # Reserve both files before network; xb prevents accidental overwrite under races.
    evidence.mkdir(parents=True,exist_ok=True)
    snapshot_path, receipt_path = evidence/'snapshot.json', Path(out).absolute()
    reserved = []
    handles = []
    try:
        for path in [receipt_path,snapshot_path]:
            handles.append(open(path,'xb'))
            reserved.append(path)
    except FileExistsError as exc:
        for handle in handles:
            handle.close()
        for path in reserved:
            path.unlink()
        raise InvalidInput('Evidence already reserved') from exc
    started, errors, item = now(), [], None
    comments, coverage, page_count = [], 'unavailable', 0
    status, end_rev = 'failed', None
    try:
        item = normalize_item(transport(item_argv(req),cfg['timeout_seconds']),req)
        comments,coverage,page_count,comment_errors = read_comments(req,cfg,transport)
        errors.extend(comment_errors)
        status = 'complete' if coverage in ('complete','empty') else 'partial'
        try:
            end_item = normalize_item(transport(item_argv(req),cfg['timeout_seconds']),req)
            end_rev = end_item['rev']
            if end_rev != item['rev']:
                status = 'unstable'
                errors.append('work_item_revision_changed')
        except (QueryFailure,OSError,ValueError) as exc:
            status = 'partial'
            errors.append(str(exc) if isinstance(exc,QueryFailure) else 'revision_recheck_failed')
    except (QueryFailure,OSError,ValueError) as exc:
        errors.append(str(exc) if isinstance(exc,QueryFailure) else 'work_item_query_failed')
    ended = now()
    snapshot = sanitize({**{k:req[k] for k in ['hu_id','change','work_item_id','organization','project_id','project_name']}, 'schema_version':1, **(item or {}),'comments':comments,'comments_sha256':digest(sanitize(comments)), 'comments_coverage':coverage,'observation_started_at_utc':started,'observation_ended_at_utc':ended,'work_item_rev_end':end_rev,'remote_text_trust':'untrusted_data_only'})
    result = {**base,'observed_at_utc':ended,'observation_started_at_utc':started,'observation_ended_at_utc':ended,'work_item_rev':item['rev'] if item else None,'work_item_rev_end':end_rev,'cli_versions':versions,'status':status,'comments_coverage':coverage,'page_count':page_count,'api_documented':API_DOCUMENTED,'api_cli_requested':API_CLI,'api_resource_revision_observed':'unknown','snapshot_ref':snapshot_path.relative_to(root).as_posix(),'snapshot_sha256':hashlib.sha256(encode(snapshot)).hexdigest(),'errors':errors,'private_evidence':'local_only_requires_review_before_publication'}
    if previous is not None and item:
        result['comparison'] = compare(previous,snapshot)
        if coverage not in ('complete','empty') or previous.get('comments_coverage') not in ('complete','empty'):
            result['comparison']['requires_reconciliation'] = True
            result['comparison']['coverage_incomplete'] = True
    # Reserved files belong to this invocation. Never reopen unrelated existing files.
    try:
        handles[1].write(encode(snapshot))
        handles[0].write(encode(sanitize(result)))
    finally:
        for handle in handles:
            handle.close()
    return sanitize(result), 0 if status == 'complete' else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['preview','read'])
    parser.add_argument('--config',required=True)
    parser.add_argument('--request',required=True)
    parser.add_argument('--out')
    args = parser.parse_args(argv)
    try:
        result,code = execute(args.operation,args.config,args.request,args.out)
    except (InvalidInput,OSError) as exc:
        result,code = {'schema_version':1,'status':'invalid_input','errors':[str(exc) if isinstance(exc,InvalidInput) else 'local_io_failed']},2
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return code
