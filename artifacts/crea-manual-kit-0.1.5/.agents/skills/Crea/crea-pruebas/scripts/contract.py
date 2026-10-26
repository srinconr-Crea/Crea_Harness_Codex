"""Selector y gate de evidencia Crea. No ejecuta comandos, Git ni APIs remotas.

Python >=3.11, biblioteca estándar. Los schemas publicados son el contrato de
intercambio; este helper aplica además sus invariantes operacionales. No es un
validador JSON Schema general ni acredita autenticidad de una ejecución.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fnmatch import fnmatchcase
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
import sys


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def canonical_bytes(path, normalization='identity'):
    payload = Path(path).read_bytes()
    if normalization == 'task_checkboxes':
        return re.sub(rb'(?m)^- \[[ \t]*[xX][ \t]*\](?= [0-9]+\.[0-9]+ )', b'- [ ]', payload)
    if normalization != 'identity':
        raise ValueError('NORMALIZATION_NOT_SUPPORTED')
    return payload


def file_hash(path, normalization='identity'):
    return hashlib.sha256(canonical_bytes(path, normalization)).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def safe_path(root, relative):
    if not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative:
        raise ValueError(f'INVALID_RELATIVE_PATH: {relative!r}')
    p = PurePosixPath(relative)
    if p.is_absolute() or '..' in p.parts or any(x in ('', '.') for x in relative.split('/')):
        raise ValueError(f'INVALID_RELATIVE_PATH: {relative!r}')
    base = Path(root).resolve()
    lexical = base / relative
    for parent in [lexical, *lexical.parents]:
        if parent == base:
            break
        if parent.is_symlink() or getattr(parent, 'is_junction', lambda: False)():
            raise ValueError('LINK_PATH_NOT_ALLOWED')
    target = (base / relative).resolve()
    if not target.is_relative_to(base):
        raise ValueError(f'PATH_OUTSIDE_REPOSITORY: {relative}')
    return target


def validate_policy(p):
    if p.get('schema_version') != '1.0' or type(p.get('setup_complete')) is not bool:
        raise ValueError('POLICY_VERSION_OR_SETUP_INVALID')
    for key in ('policy_id', 'version'):
        if not isinstance(p.get(key), str) or not p[key].strip():
            raise ValueError(f'POLICY_FIELD_MISSING: {key}')
    if not isinstance(p.get('checks'), list) or not isinstance(p.get('rules'), list):
        raise ValueError('CHECKS_AND_RULES_MUST_BE_ARRAYS')
    seen = set()
    for c in p['checks']:
        if not c.get('id') or c['id'] in seen:
            raise ValueError('DUPLICATE_OR_EMPTY_CHECK_ID')
        seen.add(c['id'])
        if c.get('environment') not in ('local', 'spark_local', 'databricks'):
            raise ValueError('INVALID_ENVIRONMENT')
        if c.get('kind') not in ('pytest', 'assertions', 'static', 'bundle', 'runtime', 'mutation', 'sast', 'eval'):
            raise ValueError('INVALID_CHECK_KIND')
        if c.get('effect') not in ('local_execution', 'remote_read', 'synthetic_write'):
            raise ValueError('INVALID_EFFECT')
        if type(c.get('configured')) is not bool or not isinstance(c.get('argv'), list):
            raise ValueError('CHECK_CONFIGURATION_INVALID')
        if not isinstance(c.get('inputs'), list) or not c['inputs']:
            raise ValueError('CHECK_INPUTS_REQUIRED')
        for key in ('inputs', 'criteria', 'required_assertions'):
            if not isinstance(c.get(key), list) or any(not isinstance(x, str) or not x for x in c[key]):
                raise ValueError(f'INVALID_CHECK_LIST: {key}')
        if not c['required_assertions'] or (c['kind'] == 'pytest' and c.get('min_tests', 0) < 1):
            raise ValueError('MEANINGFUL_ASSERTIONS_AND_PYTEST_MINIMUM_REQUIRED')
        for key in ('min_tests', 'reuse_seconds', 'timeout_seconds'):
            if type(c.get(key)) is not int or c[key] < (1 if key == 'timeout_seconds' else 0):
                raise ValueError(f'INVALID_CHECK_BOUND: {key}')
        for token in c['argv']:
            if not isinstance(token, str) or not token or '\n' in token or '\r' in token:
                raise ValueError('INVALID_ARGV_TOKEN')
    rule_ids = set()
    for rule in p['rules']:
        if not rule.get('id') or rule['id'] in rule_ids:
            raise ValueError('DUPLICATE_OR_EMPTY_RULE_ID')
        rule_ids.add(rule['id'])
        if not isinstance(rule.get('paths'), list) or not rule['paths'] or not rule.get('reason'):
            raise ValueError('RULE_PATHS_AND_REASON_REQUIRED')
        if not isinstance(rule.get('checks'), list) or set(rule['checks']) - seen:
            raise ValueError('RULE_REFERENCES_UNKNOWN_CHECK')
    return p


def snapshot(root, patterns, projection=None):
    files, missing = {}, []
    root = Path(root).resolve()
    aliases = {row['from']: row['to'] for row in (projection or {}).get('moves', [])}
    for pattern in sorted(set(patterns)):
        safe_path(root, pattern)
        # Misma semántica fnmatch que selección y dependencias. Path.glob no
        # permite que '*' cruce '/', y produciría una huella incompleta.
        if not any(char in pattern for char in '*?['):
            exact = safe_path(root, pattern)
            alias = safe_path(root, aliases[pattern]) if pattern in aliases else exact
            matches = [exact] if exact.is_file() else [alias] if alias.is_file() else []
        else:
            prefix = []
            for part in PurePosixPath(pattern).parts:
                if any(char in part for char in '*?['):
                    break
                prefix.append(part)
            start = safe_path(root, '/'.join(prefix)) if prefix else root
            matches = sorted(x for x in start.rglob('*') if x.is_file()
                             and fnmatchcase(x.relative_to(root).as_posix(), pattern))
        if not matches:
            missing.append(pattern)
        for match in matches:
            actual_name = match.relative_to(root).as_posix()
            name = next((old for old, new in aliases.items() if new == actual_name), actual_name)
            actual = safe_path(root, actual_name)
            normalization = next((row.get('normalization', 'identity') for row in (projection or {}).get('moves', [])
                                  if row['from'] == name), 'identity')
            files[name] = file_hash(actual, normalization)
    return {'files': dict(sorted(files.items())), 'missing': missing}


def build_plan(root, policy, changes, base_ref, required_criteria, provenance=None, required_check_ids=None):
    validate_policy(policy)
    root = Path(root).resolve()
    blockers, decisions, selected_rules = [], [], {}
    if not policy['setup_complete']:
        blockers.append('SETUP_INCOMPLETE')
    normalized = []
    known_checks = {c['id'] for c in policy['checks']}
    for check_id in sorted(set(required_check_ids or [])):
        if check_id not in known_checks:
            blockers.append(f'REQUIRED_CHECK_UNKNOWN: {check_id}')
        else:
            selected_rules.setdefault(check_id, set()).add('fixed-required-check-reference')
    for change in changes:
        if change.get('status') not in ('A', 'M', 'D', 'R', 'T', 'U'):
            raise ValueError('INVALID_CHANGE_STATUS')
        path, old = change.get('path'), change.get('old_path')
        safe_path(root, path)
        if change['status'] == 'R' and not old:
            raise ValueError('RENAME_REQUIRES_OLD_PATH')
        if old:
            safe_path(root, old)
        normalized.append({'status': change['status'], 'path': path, 'old_path': old})
        if change['status'] == 'U':
            blockers.append(f'UNMERGED_PATH: {path}')
        for name in sorted(set(x for x in (path, old) if x)):
            matched = [r for r in policy['rules'] if any(fnmatchcase(name, pat) for pat in r['paths'])]
            if not matched:
                blockers.append(f'UNCLASSIFIED_PATH: {name}')
            decision = ('required' if any(r['checks'] for r in matched) else 'not_applicable') if matched else 'blocked'
            decisions.append({'path': name, 'decision': decision,
                'matches': [{'rule_id': r['id'], 'reason': r['reason'], 'check_ids': r['checks']} for r in matched]})
            for r in matched:
                for check in r['checks']:
                    selected_rules.setdefault(check, set()).add(r['id'])
    # Las dependencias son declarativas: añadir inputs de un check es añadir
    # consumidores. Una modificación del fixture selecciona su check incluso
    # si una regla más general no lo menciona.
    for c in policy['checks']:
        affected = [x for x in normalized if any(
            fnmatchcase(name, pat) for name in (x['path'], x['old_path']) if name for pat in c['inputs'])]
        if affected:
            selected_rules.setdefault(c['id'], set()).add('declared-input-dependency')
    selected = []
    for c in sorted(policy['checks'], key=lambda c: c['id']):
        if c['id'] not in selected_rules:
            continue
        snap = snapshot(root, c['inputs'], (provenance or {}).get('projection'))
        if not c['configured'] or not c['argv']:
            blockers.append(f'CHECK_NOT_CONFIGURED: {c["id"]}')
        if snap['missing']:
            blockers.append(f'MISSING_CHECK_INPUT: {c["id"]}: {snap["missing"]}')
        selected.append({'check_id': c['id'], 'rule_ids': sorted(selected_rules[c['id']]),
            'input_digest': digest({'check': c, 'snapshot': snap, 'policy': digest(policy)}),
            'snapshot': snap, 'environment': c['environment'], 'effect': c['effect'], 'argv': c['argv']})
    covered = {ca for c in policy['checks'] if c['id'] in selected_rules for ca in c['criteria']}
    for ca in sorted(set(required_criteria) - covered):
        blockers.append(f'CRITERION_WITHOUT_CHECK: {ca}')
    normalized.sort(key=lambda x: (x['path'], x['old_path'] or '', x['status']))
    changed_snapshot = snapshot(root, [name for x in normalized for name in (x['path'], x['old_path']) if name],
                                (provenance or {}).get('projection'))
    plan = {'schema_version': '1.0', 'policy_id': policy['policy_id'], 'policy_version': policy['version'],
        'policy_digest': digest(policy), 'base_ref': base_ref, 'changes': normalized,
        'required_criteria': sorted(set(required_criteria)), 'decisions': sorted(decisions, key=lambda x:x['path']),
        'selected': selected, 'blockers': sorted(set(blockers)),
        'status': 'blocked' if blockers else 'ready',
        'candidate_digest': digest({'base': base_ref, 'changes': normalized, 'snapshot': changed_snapshot,
                                    'selected': selected, 'policy': digest(policy)})}
    if provenance is not None:
        plan['provenance'] = provenance
        plan['candidate_digest'] = digest({'candidate': plan['candidate_digest'], 'provenance': provenance})
    if required_check_ids is not None:
        plan['required_check_ids'] = sorted(set(required_check_ids))
    plan['plan_id'] = digest(plan)
    return plan


def can_reuse(check, prior, current_input_digest, environment_id, now=None):
    """Elegibilidad, no importación automática de un recibo a otro plan."""
    now = now or datetime.now(timezone.utc)
    try:
        ended = datetime.fromisoformat(prior['finished_at'].replace('Z', '+00:00'))
        age = (now - ended).total_seconds()
    except (KeyError, ValueError, TypeError):
        return False
    return (prior.get('status') == 'passed' and prior.get('input_digest') == current_input_digest
            and prior.get('environment_id') == environment_id and check['reuse_seconds'] > 0
            and 0 <= age <= check['reuse_seconds'])


def evaluate(root, policy, plan, results):
    blockers = []
    rebuilt = build_plan(root, policy, plan['changes'], plan['base_ref'], plan['required_criteria'], plan.get('provenance'), plan.get('required_check_ids'))
    if plan != rebuilt:
        blockers.append('STALE_OR_MODIFIED_PLAN')
    blockers.extend(plan['blockers'])
    if results.get('schema_version') != '1.0' or results.get('plan_id') != plan['plan_id'] or results.get('candidate_digest') != plan['candidate_digest']:
        blockers.append('RESULT_CANDIDATE_MISMATCH')
    checks = {c['id']: c for c in policy['checks']}
    records = results.get('records', [])
    if not isinstance(records, list):
        raise ValueError('RECORDS_MUST_BE_ARRAY')
    ids = [r.get('check_id') for r in records]
    if len(set(ids)) != len(ids):
        blockers.append('DUPLICATE_RESULT')
    expected = {x['check_id'] for x in plan['selected']}
    if set(ids) - expected:
        blockers.append('UNEXPECTED_CHECK_RESULT')
    by_id = {r.get('check_id'): r for r in records}
    for selected in plan['selected']:
        name = selected['check_id']
        c, r = checks[name], by_id.get(name)
        if not r:
            blockers.append(f'MISSING_RESULT: {name}')
            continue
        if r.get('status') != 'passed' or type(r.get('exit_code')) is not int or r.get('exit_code') != 0 or r.get('failed') != 0:
            blockers.append(f'CHECK_NOT_PASSED: {name}')
        for key in ('collected', 'executed', 'failed', 'skipped'):
            if type(r.get(key)) is not int or r[key] < 0:
                blockers.append(f'INVALID_COUNTER: {name}:{key}')
        if all(type(r.get(k)) is int for k in ('collected', 'executed', 'skipped')):
            if r['collected'] != r['executed'] + r['skipped'] or r['executed'] < c['min_tests']:
                blockers.append(f'EMPTY_OR_INCONSISTENT_SUITE: {name}')
            if r['skipped']:
                blockers.append(f'REQUIRED_SUITE_HAS_SKIPS: {name}')
        if r.get('input_digest') != selected['input_digest']:
            blockers.append(f'STALE_CHECK_INPUT: {name}')
        assertions = r.get('assertions', {})
        if not isinstance(assertions, dict) or any(assertions.get(a) != 'passed' for a in c['required_assertions']):
            blockers.append(f'REQUIRED_ASSERTION_MISSING_OR_FAILED: {name}')
        if not r.get('environment_id'):
            blockers.append(f'ENVIRONMENT_UNIDENTIFIED: {name}')
        if (c['environment'] == 'databricks' or c['effect'] in ('remote_read','synthetic_write')) and not r.get('authorization_ref'):
            blockers.append(f'REMOTE_AUTHORIZATION_REFERENCE_MISSING: {name}')
        try:
            start = datetime.fromisoformat(r['started_at'].replace('Z', '+00:00'))
            finish = datetime.fromisoformat(r['finished_at'].replace('Z', '+00:00'))
            if start.tzinfo is None or finish.tzinfo is None or finish < start:
                raise ValueError('Invalid order or timezone')
        except (KeyError, ValueError, TypeError):
            blockers.append(f'INVALID_TIMESTAMPS: {name}')
        if not r.get('evidence'):
            blockers.append(f'EVIDENCE_MISSING: {name}')
        for entry in r.get('evidence', []):
            try:
                p = safe_path(root, entry['path'])
                if not p.is_file() or file_hash(p) != entry['sha256']:
                    blockers.append(f'EVIDENCE_HASH_MISMATCH: {name}')
            except (KeyError, ValueError, OSError):
                blockers.append(f'EVIDENCE_UNREADABLE: {name}')
    return {'schema_version':'1.0', 'plan_id':plan['plan_id'],
            'status':'blocked' if blockers else 'passed', 'blockers':sorted(set(blockers)),
            'scope':'technical_test_evidence_only', 'allows_deploy':False, 'allows_archive':False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    for mode in ('validate-policy', 'plan', 'gate'):
        p = sub.add_parser(mode)
        p.add_argument('--policy', required=True, type=Path)
        if mode != 'validate-policy':
            p.add_argument('--repo', required=True, type=Path)
        if mode == 'plan':
            p.add_argument('--changes', required=True, type=Path, help='Objeto con changes y required_criteria')
            p.add_argument('--base', required=True, help='SHA de base verificado; nunca una rama inferida')
        if mode == 'gate':
            p.add_argument('--plan', required=True, type=Path)
            p.add_argument('--results', required=True, type=Path)
        p.add_argument('--out', type=Path)
    args = parser.parse_args()
    try:
        policy = validate_policy(read_json(args.policy))
        if args.mode == 'validate-policy':
            result = {'valid':True, 'setup_complete':policy['setup_complete']}
        elif args.mode == 'plan':
            scope = read_json(args.changes)
            result = build_plan(args.repo, policy, scope['changes'], args.base, scope['required_criteria'])
        else:
            result = evaluate(args.repo, policy, read_json(args.plan), read_json(args.results))
        output = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(output, encoding='utf-8')
        else:
            print(output, end='')
        return 2 if result.get('status') == 'blocked' else 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(json.dumps({'status':'blocked','error':str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
