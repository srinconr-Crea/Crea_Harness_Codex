"""Resolver e inspeccionar entrega; snapshot remoto solo por operación explícita."""
import argparse
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit
from subprocess import SubprocessError

from team_common import (CONTRACTS, file_hash, git, git_result, hu_export, identity, process,
                         read, safe_path, utc, validate_data)
from testing.git_adapter import parse_diff
from testing.common import KIT


def branch(name):
    if not isinstance(name, str) or not name or name.startswith('-') or any(c in name for c in '\n\r\0'):
        raise ValueError('BRANCH_NAME_INVALID')
    if process(['git', 'check-ref-format', 'refs/heads/' + name]).returncode:
        raise ValueError('BRANCH_NAME_INVALID')
    return name


def resolve(project):
    delivery = project['delivery']
    base = branch(project['project']['base_branch'])
    configured_target = delivery.get('pr_target_branch')
    target = branch(base if configured_target is None else configured_target)
    remote = delivery['remote']
    if not isinstance(remote, str) or not re.fullmatch(r'[A-Za-z0-9_./-]+', remote) or remote.startswith('-'):
        raise ValueError('REMOTE_NAME_INVALID')
    branch('remotes/' + remote + '/probe')
    return {'base_branch': base, 'target_branch': target, 'remote': remote}


def validate_feature(project, feature):
    settings = resolve(project)
    denied = set(project['delivery'].get('protected_branches', []))
    denied.update([settings['base_branch'], settings['target_branch']])
    if project['delivery'].get('pr_target_branch') or project['delivery'].get('compatibility', {}).get('enabled'):
        denied.update(['quality', 'test'])
    branch(feature)
    if feature in denied or not feature.startswith(project['delivery']['branch_prefix']):
        raise ValueError('FEATURE_BRANCH_NOT_ALLOWED')
    return feature


def repository_key(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('REPOSITORY_URL_REQUIRED')
    if any(c in value for c in '\r\n\0'):
        raise ValueError('REPOSITORY_URL_INVALID')
    if re.match(r'^[^/@:]+@[^/:]+:', value):
        host, path = value.split('@', 1)[1].split(':', 1)
    elif '://' in value:
        parsed = urlsplit(value)
        public_azure_user = (parsed.hostname == 'dev.azure.com' and parsed.username
                             and parsed.username.casefold() == parsed.path.strip('/').split('/')[0].casefold())
        if parsed.password or (parsed.username and parsed.scheme != 'ssh' and not public_azure_user) or parsed.query or parsed.fragment:
            raise ValueError('CREDENTIALS_IN_REPOSITORY_URL')
        host, path = parsed.hostname, parsed.path
        if not host:
            raise ValueError('REPOSITORY_URL_INVALID')
    else:
        return ('local', str(Path(value).resolve()).casefold())
    path = path.strip('/').removesuffix('.git')
    if host.lower() == 'ssh.dev.azure.com' and path.startswith('v3/'):
        return ('azure', *path[3:].lower().split('/'))
    if host.lower() == 'dev.azure.com':
        return ('azure', *path.replace('/_git/', '/').lower().split('/'))
    if host.lower().endswith('.visualstudio.com'):
        return ('azure', host.lower().removesuffix('.visualstudio.com'), *path.replace('/_git/', '/').lower().split('/'))
    return (host.lower(), path.casefold())


def verified_remote(root, project):
    settings = resolve(project)
    actual = git(root, 'remote', 'get-url', settings['remote'])
    if repository_key(actual) != repository_key(project['project']['repository']['url']):
        raise ValueError('REPOSITORY_IDENTITY_MISMATCH')
    return settings


def inspect_local(root, project, feature, expected_sha=None):
    settings = verified_remote(root, project)
    validate_feature(project, feature)
    issues = []
    if Path(git(root, 'rev-parse', '--show-toplevel')).resolve() != Path(root).resolve():
        issues.append('NOT_REPOSITORY_ROOT')
    current = git(root, 'branch', '--show-current')
    head = git(root, 'rev-parse', '--verify', 'HEAD^{commit}')
    if current != feature:
        issues.append('CURRENT_BRANCH_MISMATCH')
    if expected_sha and head != expected_sha:
        issues.append('CANDIDATE_SHA_CHANGED')
    if git(root, 'status', '--porcelain=v1', '--untracked-files=all'):
        issues.append('DIRTY_CHECKOUT')
    return {'schema_version':'1.0', **settings, 'source_branch':feature, 'head_sha':head,
            'issues':issues, 'ready':not issues}


def delta(root, before, after):
    raw = git_result(root, 'diff', '--no-ext-diff', '--no-textconv', '--name-status', '-z', '-M', before, after, '--')
    if raw.returncode:
        raise ValueError('GIT_DIFF_UNAVAILABLE')
    return parse_diff(raw.stdout)


def ranges(root, birth, head, target):
    b = git(root, 'rev-parse', '--verify', birth + '^{commit}')
    h = git(root, 'rev-parse', '--verify', head + '^{commit}')
    q = git(root, 'rev-parse', '--verify', target + '^{commit}')
    git(root, 'merge-base', '--is-ancestor', b, h)
    common = git(root, 'merge-base', '--all', b, q).splitlines()
    if len(common) != 1:
        raise ValueError('HISTORY_REQUIRES_REVIEW')
    m = common[0]
    return {'branch_start_sha':b, 'source_sha':h, 'target_sha':q, 'merge_bases':common,
            'story_changes':delta(root,b,h), 'target_changes':delta(root,m,q),
            'inherited_changes':delta(root,m,b),
            'inherited_commits':git(root,'rev-list',q+'..'+b).splitlines(),
            'pr_commits':git(root,'rev-list',q+'..'+h).splitlines()}


def remote_sha(root, remote, target):
    result = git_result(root, 'ls-remote', '--exit-code', '--heads', remote, 'refs/heads/' + branch(target))
    if result.returncode == 2:
        return None, 'missing'
    if result.returncode:
        error = result.stderr.decode('utf-8', errors='replace').lower()
        state = 'access_denied' if any(x in error for x in ['authentication failed','permission denied','access denied','403','401']) else 'connection_error'
        return None, state
    lines = result.stdout.decode('utf-8').splitlines()
    if len(lines) != 1:
        return None, 'unverified'
    fields = lines[0].split()
    if len(fields) != 2 or fields[1] != 'refs/heads/' + target or not re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}',fields[0]):
        return None, 'unverified'
    return fields[0], 'verified'


def check_scope(root, project, handoff):
    """Delivery scope is mandatory for the new target even without advisory compatibility."""
    provenance=handoff['scope'].get('git_delivery')
    required=project['delivery'].get('pr_target_branch') is not None or provenance is not None
    result={'required':required,'issues':[]}
    if not required:return result
    if not provenance:
        result['issues'].append('DELIVERY_SOURCE_PROVENANCE_REQUIRED');return result
    ref=handoff['evidence'].get('target_snapshot')
    if not ref or not ref.get('sha256'):
        result['issues'].append('DELIVERY_SCOPE_SNAPSHOT_REQUIRED');return result
    try:
        settings=verified_remote(root,project)
        current=git(root,'branch','--show-current');validate_feature(project,current)
        if current!=provenance['source_branch'] or provenance['remote']!=settings['remote']:
            raise ValueError('DELIVERY_SOURCE_MISMATCH')
        path=safe_path(root,ref['path'])
        if file_hash(path)!=ref['sha256']:raise ValueError('DELIVERY_SNAPSHOT_CHANGED')
        snapshot=read(path)
        from testing.schemas import validate_schema
        validate_schema(read(KIT/'docs/plantillas/git-target-snapshot.schema.json'),snapshot)
        if (snapshot['change']!=handoff['identity']['change'] or snapshot['status']!='verified'
            or not snapshot['objects_available'] or snapshot['target_branch']!=settings['target_branch']
            or snapshot['remote']!=settings['remote']
            or snapshot['repository']!=list(repository_key(project['project']['repository']['url']))):
            raise ValueError('DELIVERY_SCOPE_DESTINATION_NOT_VERIFIED')
        computed=ranges(root,provenance['branch_start_sha'],'HEAD',snapshot['target_sha'])
        result['ranges']=computed
        accepted=set(provenance.get('approved_inherited_commits',[]))
        if set(computed['inherited_commits'])-accepted:
            result['issues'].append('INHERITED_DELIVERY_SCOPE_REQUIRES_DECISION')
    except (ValueError,OSError,KeyError,TypeError) as exc:
        result['issues'].append(str(exc) if isinstance(exc,ValueError) else 'DELIVERY_SCOPE_UNVERIFIED')
    return result


def snapshot(root, project, change, attempt):
    identity(change); identity(attempt)
    settings = verified_remote(root, project)
    sha, state = remote_sha(root, settings['remote'], settings['target_branch'])
    value = {'schema_version':'1.0', 'kind':'git_target_snapshot', 'change':change, 'attempt':attempt,
             'repository':list(repository_key(project['project']['repository']['url'])), **settings,
             'target_sha':sha, 'observed_at':utc(), 'status':state, 'objects_available':False,
             'git_version':git(root,'--version'), 'limits':[]}
    if sha:
        ref = 'refs/crea/snapshots/' + change + '/' + attempt
        if git_result(root,'show-ref','--verify','--quiet',ref).returncode == 0:
            raise ValueError('SNAPSHOT_REF_OCCUPIED')
        result = git_result(root,'-c','core.hooksPath=' + os.devnull,
                            'fetch','--no-tags','--no-write-fetch-head','--recurse-submodules=no',settings['remote'],
                            'refs/heads/'+settings['target_branch']+':'+ref)
        if result.returncode or git(root,'rev-parse',ref) != sha:
            value['status']='unverified'; value['limits'].append('REMOTE_CHANGED_OR_FETCH_FAILED')
        else:
            latest, latest_state = remote_sha(root,settings['remote'],settings['target_branch'])
            if latest_state != 'verified' or latest != sha:
                value['status']='unverified'; value['limits'].append('REMOTE_CHANGED_DURING_SNAPSHOT')
            else:
                value['objects_available']=True
    validate_data(root,'docs/plantillas/git-target-snapshot.schema.json',value)
    return value


def freshness(root, project, observation):
    settings = verified_remote(root,project)
    sha, state = remote_sha(root,settings['remote'],settings['target_branch'])
    return {**observation,'target_sha':sha,'observed_at':utc(), 'status':state,
            'objects_available':bool(sha and git_result(root,'cat-file','-e',sha+'^{commit}').returncode==0),
            'limits':[] if state=='verified' else ['FINAL_REMOTE_RECHECK_UNVERIFIED']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['inspect','snapshot','freshness','scope'],nargs='?')
    parser.add_argument('--describe-contracts',action='store_true')
    parser.add_argument('--repo',type=Path); parser.add_argument('--feature'); parser.add_argument('--sha')
    parser.add_argument('--change'); parser.add_argument('--attempt'); parser.add_argument('--out'); parser.add_argument('--snapshot')
    parser.add_argument('--handoff')
    args=parser.parse_args()
    if args.describe_contracts: print(json.dumps(CONTRACTS)); return 0
    try:
        if not args.repo or not args.action: raise ValueError('EXPLICIT_REPO_AND_ACTION_REQUIRED')
        root=args.repo.resolve(); project=read(safe_path(root,'docs/proyecto.json'))
        if args.action=='snapshot': value=snapshot(root,project,args.change,args.attempt)
        elif args.action=='freshness': value=freshness(root,project,read(safe_path(root,args.snapshot)))
        elif args.action=='scope': value=check_scope(root,project,read(safe_path(root,args.handoff)))
        else: value=inspect_local(root,project,args.feature,args.sha)
        if args.out: hu_export(root,args.out,value,args.change)
        print(json.dumps(value,ensure_ascii=False)); return 0
    except (ValueError,OSError,KeyError,TypeError,SubprocessError) as exc:
        print(json.dumps({'status':'undetermined','error':str(exc) if isinstance(exc,ValueError) else type(exc).__name__})); return 4


if __name__=='__main__':
    raise SystemExit(main())
