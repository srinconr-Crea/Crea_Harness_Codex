"""Contratos locales Crea. Inspecciona y renderiza; nunca ejecuta suites o publica."""
import argparse
from fnmatch import fnmatchcase
import json
from pathlib import Path
import re
from urllib.parse import quote, urlencode, urlparse, parse_qs

DEPENDENCY_ERROR = None
try:
    from testing import git_adapter, schemas, workflow
    from testing.common import KIT, read, safe_path, digest, file_hash, render_handoff, resolve_reference
except ImportError as exc:
    DEPENDENCY_ERROR = type(exc).__name__

TRANSITIONS = ('to_apply', 'to_test', 'to_review', 'to_sync', 'to_archive', 'to_publish', 'to_pr')
PHASES = '(planificacion|implementacion|pruebas|revision|cierre|entrega)'
TECHNICAL = ('to_review', 'to_sync', 'to_archive', 'to_publish', 'to_pr')


def select_rules(root, project, layers, capabilities, not_applicable_reason):
    if not layers and not capabilities and not not_applicable_reason:
        raise ValueError('NOT_APPLICABLE_REASON_REQUIRED')
    config = project.get('rules')
    if not config or not config['enabled']:
        return []
    if not safe_path(root, config['index_path']).is_file():
        raise ValueError('RULE_INDEX_MISSING')
    paths = list(config['common'])
    for category, selection in [('layers', layers), ('capabilities', capabilities)]:
        for name in selection:
            if name not in config[category]:
                raise ValueError('RULE_SELECTION_NOT_CONFIGURED: ' + name)
            paths.append(config[category][name])
    result, seen = [], set()
    for name in dict.fromkeys(paths):
        path = safe_path(root, name)
        if not path.is_file():
            raise ValueError('RULE_DOCUMENT_MISSING: ' + name)
        text = path.read_text(encoding='utf-8-sig')
        if not re.search(r'^Estado: active\s*$', text, re.M):
            raise ValueError('RULE_DOCUMENT_NOT_ACTIVE: ' + name)
        revision = re.search(r'^Revisión: (.+)$', text, re.M)
        if not revision:
            raise ValueError('RULE_REVISION_REQUIRED: ' + name)
        blocks = re.split(r'^### ([A-Za-z0-9][A-Za-z0-9_-]+)\s*$', text, flags=re.M)
        if len(blocks) < 3:
            raise ValueError('ACTIVE_RULE_DOCUMENT_EMPTY: ' + name)
        for index in range(1, len(blocks), 2):
            rule_id, body = blocks[index:index+2]
            mode = re.search(r'^Comprobación: (automatic|review|human_decision)\s*$', body, re.M)
            if rule_id in seen or not mode:
                raise ValueError('RULE_ID_OR_CHECK_MODE_INVALID: ' + name)
            seen.add(rule_id)
            result.append({'id': rule_id, 'path': name, 'revision': revision[1].strip(),
                           'sha256': file_hash(path), 'check_mode': mode[1]})
    return result


def validate_handoff(root, name):
    h = read(safe_path(root, name))
    schemas.validate_schema(read(KIT / 'docs/plantillas/handoff.schema.json'), h)
    identity = h['identity']
    expected = f"docs/hu/{identity['change']}/handoffs/{identity['phase']}-{identity['attempt']}.json"
    if name != expected:
        raise ValueError('HANDOFF_IDENTITY_MISMATCH')
    if h['previous_handoff'] and h['previous_handoff']['path'] == name:
        raise ValueError('CIRCULAR_HANDOFF_REFERENCE')
    git_adapter.validate_predecessor(root, h, name)
    return h


def render(root, name):
    h = validate_handoff(root, name)
    return render_handoff(h, name, file_hash(safe_path(root, name)))


def save(root, name, content, change):
    prefix = 'docs/hu/' + change + '/'
    if not name.startswith(prefix):
        raise ValueError('OUTPUT_OUTSIDE_CASE')
    suffix = name[len(prefix):]
    if suffix not in ('resumen.md', 'evidencia.md', 'pr.md', 'pr-title.txt', 'pr-body.md') and not re.fullmatch(
            r'handoffs/' + PHASES + r'-[1-9][0-9]*(?:-(entrada|salida|informe))?\.json', suffix):
        raise ValueError('OUTPUT_ROLE_NOT_ALLOWED')
    path = safe_path(root, name)
    if path.exists():
        raise ValueError('OUTPUT_ALREADY_EXISTS_USE_NEW_ATTEMPT')
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(content)
    except FileExistsError as exc:
        raise ValueError('OUTPUT_ALREADY_EXISTS_USE_NEW_ATTEMPT') from exc


def reference(root, ref, moves=()):
    return resolve_reference(root, ref, moves)


def delivery_digest(content):
    # The resulting commit is checked separately against the tested candidate. It
    # cannot participate in the digest of the content approved before commit.
    return digest({k: content[k] for k in ('title', 'body', 'repository', 'source_branch', 'target_branch')})


def github_form(content):
    repo = urlparse(content['repository'])
    if repo.scheme != 'https' or repo.hostname != 'github.com' or repo.username or repo.password or repo.query or repo.fragment:
        raise ValueError('GITHUB_WEB_REPOSITORY_REQUIRED')
    if len(repo.path.strip('/').removesuffix('.git').split('/')) != 2:
        raise ValueError('GITHUB_WEB_REPOSITORY_REQUIRED')
    query = urlencode({'quick_pull': '1', 'title': content['title'], 'body': content['body']})
    url = content['repository'].removesuffix('.git').rstrip('/') + '/compare/' + quote(content['target_branch'], safe='') + '...' + quote(content['source_branch'], safe='') + '?' + query
    decoded = parse_qs(urlparse(url).query)
    if decoded.get('title') != [content['title']] or decoded.get('body') != [content['body']]:
        raise ValueError('PR_FORM_CONTENT_NOT_CONFIRMED')
    return url


def verify_pr(expected, observed):
    normalize = lambda value: value.replace('\r\n', '\n').removesuffix('\n')
    fields = ('title', 'body', 'repository', 'source_branch', 'target_branch', 'head_sha')
    return bool(observed.get('id') and observed.get('url') and observed.get('state') in ('active', 'draft', 'open')
                and all(isinstance(observed.get(k), str) and normalize(observed[k]) == normalize(expected[k]) for k in fields))


def consume(report, code, mode, existing_constraints=None, blocking_conditions=()):
    """Caller passes independently checked previous controls, especially after exit 4."""
    valid = isinstance(report, dict) and report.get('check_status') == 'completed' and code in (0, 2, 3)
    findings = report.get('findings', []) if isinstance(report, dict) else []
    decision = code == 3 and any(x.get('class') == 'human_decision_pending' for x in findings)
    error = not valid or (code == 2 and mode == 'informative') or (code == 3 and not decision)
    if existing_constraints is None:
        can_continue = None
    else:
        can_continue = not existing_constraints and not decision
        if mode == 'enforcing' and ((error and blocking_conditions)
                or (isinstance(report, dict) and report.get('new_control_effect') == 'block')):
            can_continue = False
    return {'can_continue': can_continue, 'validation': 'undetermined' if error else 'completed',
            'scope': 'requested_transition_only', 'independent_authorized_work': True,
            'existing_constraints': existing_constraints}


def check(root, name, transition, operation=None):
    if transition not in TRANSITIONS:
        raise ValueError('TRANSITION_NOT_SUPPORTED')
    report = {'kind': 'transition_report', 'schema_version': '1.0', 'change': 'unknown', 'handoff': name,
              'transition': transition, 'mode': 'informative', 'check_status': 'completed',
              'new_control_effect': 'allow', 'existing_constraints': [], 'findings': [], 'exit_code': 0, 'observation': None}
    enabled = []
    def finding(condition, reason, owner, correction, classification='blocking_noncompliance', observed=None, recheck=None):
        report['findings'].append({'condition_id': condition, 'class': classification,
          'observed': observed or reason, 'reason': reason, 'transition': transition,
          'correction': correction, 'owner': owner, 'preserved_evidence': ['Artefactos primarios no alterados; sujeto al gate vigente'],
          'recheck': recheck or ['Contrato y condición afectada; no ejecutar suites desde este validador']})
    try:
        project = schemas.validate('project', read(safe_path(root, 'docs/proyecto.json')))
        settings = project['workflow'].get('transitions', {'mode': 'informative', 'blocking_conditions': []})
        report['mode'], enabled = settings['mode'], settings['blocking_conditions']
        if report['mode'] == 'enforcing' and enabled:
            reference(root, {'path': settings['promotion_ref']})
        h = read(safe_path(root, name))
        report['change'] = h.get('identity', {}).get('change', 'unknown')
        try:
            validate_handoff(root, name)
        except ValueError as exc:
            finding('TRANSITION_FIELDS', str(exc), 'principal', 'Corregir el contrato en un nuevo intento sin alterar evidencia primaria')
        if h['continuation']['transition'] != transition:
            finding('IDENTITY_MATCH', 'REQUESTED_TRANSITION_MISMATCH', 'principal', 'Seleccionar el handoff y transición correspondientes')
        context = h['context']
        selected = select_rules(root, project, context['layers'], context['capabilities'], context['not_applicable_reason'])
        if selected != context['rules']:
            finding('REFERENCE_EXISTS', 'RULE_SELECTION_OR_REVISION_CHANGED', 'planner', 'Reconciliar la selección compartida; decidir cambios sustantivos antes de Apply')
        refs = h['scope']['criteria'] + context['functional_decisions'] + h['evidence']['artifacts'] + h['evidence']['decisions']
        if h['previous_handoff']:
            refs.append(h['previous_handoff'])
        if h['evidence']['validation_plan']:
            refs.append(h['evidence']['validation_plan'])
        for rule in context['rules']:
            refs.append({'path': rule['path'], 'sha256': rule['sha256']})
        for obj in h['evidence']['objects']:
            for state in ('implementation', 'deployment', 'verification'):
                refs.extend(obj[state]['references'])
        for ref in refs:
            try:
                reference(root, ref, h['scope']['moves'])
            except (ValueError, OSError) as exc:
                finding('REFERENCE_EXISTS', str(exc) if isinstance(exc, ValueError) else 'REFERENCE_IO_ERROR',
                        h['identity']['sender'], 'Corregir la referencia o aportar evidencia real; no repetir pruebas si el recibo válido ya existe')
        if transition == 'to_apply' and not project['project']['setup_complete']:
            report['existing_constraints'].append('PROJECT_SETUP_INCOMPLETE')
        if transition == 'to_publish' and operation not in ('commit', 'push'):
            report['existing_constraints'].append('PUBLICATION_OPERATION_REQUIRED')
        actions = {'to_apply': ['apply'], 'to_archive': ['archive'], 'to_publish': [operation] if operation in ('commit', 'push') else ['commit', 'push'],
                   'to_pr': ['create_pr'] if 'create_pr' in h['scope']['actions'] else []}.get(transition, [])
        authorization = h['continuation']['authorization']
        authorized = not actions
        if actions and authorization:
            try:
                reference(root, authorization['response_ref'], h['scope']['moves'])
                authorized = (not set(actions) - set(authorization['actions'])
                              and authorization['context_digest'] == digest(git_adapter.handoff_context(h))
                              and authorization['candidate_digest'] == h['scope']['candidate_digest'])
                if transition in ('to_publish', 'to_pr'):
                    authorized = authorized and bool(h['evidence']['delivery']) and authorization['delivery_digest'] == delivery_digest(h['evidence']['delivery'])
            except (ValueError, OSError):
                authorized = False
        if not authorized:
            reason = 'APPLY_AUTHORIZATION_MISSING' if transition == 'to_apply' else 'ACTION_AUTHORIZATION_MISSING_OR_STALE'
            report['existing_constraints'].append(reason)
            finding('AUTHORIZATION_SCOPE', reason, 'principal', 'Obtener o referenciar la respuesta humana aplicable a estas acciones y candidato', 'human_decision_pending')
        decision = h['continuation']['decision_required']
        questions = h['pending']['questions'] + ([decision] if decision else [])
        for question in questions:
            if transition in question['transitions']:
                finding('NO_REQUIRED_BLOCKERS', question['reason'], question['owner'], 'Resolver la decisión y reanudar solo lo dependiente', 'human_decision_pending')
        for blocker in h['pending']['blockers']:
            if transition in blocker['transitions']:
                finding('NO_REQUIRED_BLOCKERS', blocker['reason'], blocker['owner'], 'Corregir el pendiente concreto; preservar trabajo independiente')
        observation = git_adapter.observe(root)
        report['observation'] = observation
        snapshots = {}
        for key in ('entry', 'exit'):
            ref = h['scope'][key]
            if ref:
                baseline = read(reference(root, ref, h['scope']['moves']))
                schema = read(KIT / 'docs/plantillas/handoff.schema.json')
                schemas.validate_schema({'$defs': schema['$defs'], '$ref': '#/$defs/snapshot'}, baseline)
                snapshots[key] = baseline
        def allowed(path):
            if path == '.git/HEAD':
                return 'commit' in h['scope']['actions']
            if path == '.git/branch':
                return 'switch_branch' in h['scope']['actions']
            if path == '.git/index':
                return bool({'stage', 'commit'} & set(h['scope']['actions']))
            return any(fnmatchcase(path, pattern) for pattern in h['scope']['write_paths'])
        if 'entry' in snapshots:
            end = snapshots.get('exit', observation)
            delta = git_adapter.scope_changes(snapshots['entry'], end)
            unexpected = [path for path in delta if not allowed(path)]
            if unexpected:
                finding('WRITE_SCOPE', 'OBSERVED_CHANGES_OUTSIDE_ROLE_SCOPE' if 'exit' in snapshots else 'OPEN_INTERVAL_WRITER_UNCERTAIN',
                        h['identity']['sender'] if 'exit' in snapshots else 'principal',
                        'Resolver esas rutas/acciones o reconciliar la autoría; no reiniciar la HU', observed=', '.join(unexpected))
        if 'exit' in snapshots:
            later = git_adapter.scope_changes(snapshots['exit'], observation)
            registered = {name}
            registered.update(h['scope'][key]['path'] for key in ('entry', 'exit') if h['scope'][key])
            later = [path for path in later if path not in registered]
            if later:
                finding('WRITE_SCOPE', 'POST_HANDOFF_CHANGES_REQUIRE_RECONCILIATION', 'principal',
                        'Contrastar cambios posteriores con su escritor/alcance; no atribuirlos al rol cerrado',
                        'warning', observed=', '.join(later))
        if not h['scope']['entry']:
            finding('WRITE_SCOPE', 'ENTRY_SNAPSHOT_UNAVAILABLE', 'principal', 'Capturar una referencia real antes del siguiente escritor; no inventar autoría', 'warning')
        if transition in TECHNICAL:
            tests = h['evidence']['tests']
            try:
                if not tests:
                    raise ValueError('REQUIRED_TEST_EVIDENCE_MISSING')
                plan = read(reference(root, tests['plan'], h['scope']['moves']))
                results = read(reference(root, tests['results'], h['scope']['moves']))
                configured = project['validation']['testing']
                gate = workflow.gate(root, safe_path(root, configured['policy_path']), safe_path(root, configured['execution_path']), plan, results)
                if gate['status'] != 'passed':
                    raise ValueError('; '.join(gate['blockers']))
                if h['scope']['candidate_digest'] != plan['candidate_digest']:
                    raise ValueError('HANDOFF_TEST_CANDIDATE_MISMATCH')
            except (ValueError, OSError, KeyError, TypeError) as exc:
                report['existing_constraints'].append('REQUIRED_GATE_NOT_SATISFIED')
                finding('EVIDENCE_CURRENT', str(exc) if isinstance(exc, ValueError) else 'GATE_EVIDENCE_UNAVAILABLE',
                        'principal', 'Reconciliar con plan/run/gate; Tester ejecuta solo lo requerido tras cambios reales')
        if transition in ('to_sync', 'to_archive', 'to_publish', 'to_pr'):
            kinds = {ref.get('kind') for ref in h['evidence']['artifacts']}
            if not {'review', 'verify'}.issubset(kinds) or h['result']['status'] in ('blocked', 'needs_changes'):
                report['existing_constraints'].append('FAVORABLE_REVIEW_AND_VERIFY_REQUIRED')
        if transition in ('to_publish', 'to_pr') and not project['delivery']['enabled']:
            report['existing_constraints'].append('DELIVERY_DISABLED')
        publication_paths = authorization.get('publication_paths', h['scope']['approved_paths']) if authorization else h['scope']['approved_paths']
        if transition == 'to_publish' and operation == 'commit':
            git_adapter.verify_index(root, publication_paths)
        if transition == 'to_publish' and operation == 'push' and 'REQUIRED_GATE_NOT_SATISFIED' not in report['existing_constraints']:
            delivery = h['evidence']['delivery']
            head = git_adapter.git(root, 'rev-parse', 'HEAD').decode().strip()
            if not delivery or delivery['head_sha'] != head:
                report['existing_constraints'].append('LOCAL_COMMIT_NOT_CONFIRMED_BEFORE_PUSH')
            else:
                projection = plan.get('provenance', {}).get('projection')
                if not projection:
                    report['existing_constraints'].append('COMMIT_EQUIVALENCE_NOT_SUPPORTED_FOR_LEGACY_PLAN')
                else:
                    policy, execution = workflow.load(safe_path(root, configured['policy_path']), safe_path(root, configured['execution_path']))
                    view = git_adapter.content_view(root, plan['base_ref'], execution['outputs'], projection,
                                                   [p for c in policy['checks'] for p in c['inputs']])
                    try:
                        git_adapter.verify_commit(root, plan['base_ref'], head, view, publication_paths)
                    except ValueError as exc:
                        report['existing_constraints'].append('COMMIT_NOT_EQUIVALENT_BEFORE_PUSH')
                        finding('EVIDENCE_CURRENT', str(exc), 'principal', 'Corregir árbol/rango antes de push y volver a comprobar evidencia vigente')
        if transition == 'to_pr':
            delivery = h['evidence']['delivery']
            if not delivery or not delivery.get('push_ref'):
                report['existing_constraints'].append('PUSH_NOT_CONFIRMED')
            else:
                pushed = read(reference(root, delivery['push_ref']))
                if any(pushed.get(k) != delivery[k] for k in ('repository', 'source_branch', 'head_sha')):
                    report['existing_constraints'].append('PUSH_IDENTITY_MISMATCH')
                if git_adapter.git(root, 'rev-parse', 'HEAD').decode().strip() != delivery['head_sha']:
                    report['existing_constraints'].append('PUSHED_COMMIT_NOT_LOCAL_HEAD')
                if 'REQUIRED_GATE_NOT_SATISFIED' not in report['existing_constraints']:
                    projection = plan.get('provenance', {}).get('projection')
                    if projection:
                        policy, execution = workflow.load(safe_path(root, configured['policy_path']), safe_path(root, configured['execution_path']))
                        view = git_adapter.content_view(root, plan['base_ref'], execution['outputs'], projection,
                                                       [p for c in policy['checks'] for p in c['inputs']])
                        git_adapter.verify_commit(root, plan['base_ref'], delivery['head_sha'], view, publication_paths)
                if delivery['status'] == 'created_verified':
                    if not delivery.get('observed_ref') or not verify_pr(delivery, read(reference(root, delivery['observed_ref']))):
                        report['existing_constraints'].append('PR_CONTENT_OR_IDENTITY_NOT_CONFIRMED')
        human = any(f['class'] == 'human_decision_pending' for f in report['findings'])
        blocking = report['mode'] == 'enforcing' and any(f['class'] == 'blocking_noncompliance' and f['condition_id'] in enabled for f in report['findings'])
        report['new_control_effect'] = 'block' if blocking else 'report_only' if report['findings'] else 'allow'
        report['exit_code'] = 3 if human else 2 if blocking else 0
    except (ValueError, OSError, KeyError, TypeError, ImportError) as exc:
        report['check_status'], report['new_control_effect'], report['exit_code'] = 'validator_error', 'undetermined', 4
        finding('TRANSITION_FIELDS', str(exc) if isinstance(exc, ValueError) else type(exc).__name__,
                'principal', 'Resolver la comprobación no completada y consultar controles previos por sus mecanismos actuales', 'validator_error')
    return report


def main():
    if DEPENDENCY_ERROR:
        print(json.dumps({'check_status': 'validator_error', 'reason': 'DEPENDENCY_UNAVAILABLE',
                          'new_control_effect': 'undetermined', 'exit_code': 4}))
        return 4
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'render'])
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--handoff', required=True)
    parser.add_argument('--transition', choices=TRANSITIONS)
    parser.add_argument('--operation', choices=['commit', 'push'], help='Paso de entrega de to_publish; push comprueba el commit antes de publicar')
    parser.add_argument('--out')
    args = parser.parse_args()
    if args.action == 'check' and not args.transition:
        parser.error('--transition is required for check')
    try:
        if args.action == 'render':
            output = render(args.repo, args.handoff)
            change = validate_handoff(args.repo, args.handoff)['identity']['change']
            code = 0
        else:
            report = check(args.repo, args.handoff, args.transition, args.operation)
            output, change, code = json.dumps(report, ensure_ascii=False, indent=2) + '\n', report['change'], report['exit_code']
        if args.out:
            save(args.repo, args.out, output, change)
        print(output, end='')
        return code
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({'check_status': 'validator_error', 'reason': str(exc) if isinstance(exc, ValueError) else type(exc).__name__}))
        return 4


if __name__ == '__main__':
    raise SystemExit(main())
