"""Acciones separadas plan/run/gate. Planificar nunca ejecuta suites."""
from datetime import datetime, timezone
from fnmatch import fnmatchcase
from pathlib import Path
import platform

from . import execution, git_adapter, reports, schemas, catalog, attempts
from .common import ASSETS, KIT, contract, digest, file_hash, read, safe_path, write


def load(policy_path, settings_path):
    policy = schemas.validate('policy', read(policy_path))
    settings = schemas.validate('execution', read(settings_path))
    contract.validate_policy(policy)
    git_adapter.validate_outputs(settings['outputs'])
    for check in policy['checks']:
        for output in settings['outputs']:
            if any(fnmatchcase(output, pat) for pat in check['inputs']):
                raise ValueError('GENERATED_OUTPUT_IS_A_CHECK_INPUT')
    return policy, settings


def adapter_digest(context=False):
    paths = sorted((KIT / 'scripts/crea/testing').glob('*.py'))
    paths += sorted(ASSETS.glob('*.schema.json'))
    paths += [ASSETS.parent / 'scripts/contract.py', KIT / 'scripts/crea/pruebas.py', KIT / 'scripts/crea/run_pytest.py']
    paths += [KIT / 'docs/plantillas/handoff.schema.json', KIT / 'scripts/crea/transiciones.py']
    if context:
        paths += [KIT / 'scripts/crea/contexto.py']
    return digest({p.relative_to(KIT).as_posix(): file_hash(p) for p in paths})


def projection_for(root, project, settings):
    if not project or 'transitions' not in project['workflow']:
        return None
    import re
    changes = {m[1] for path in settings['outputs']
               if (m := re.match(r'docs/hu/([a-zA-Z0-9_-]+)/pruebas/', path))}
    if len(changes) != 1:
        return None
    change = next(iter(changes))
    parent = Path(root) / 'docs/hu' / change / 'handoffs'
    paths = [p for p in parent.glob('planificacion-*.json')
             if re.fullmatch(r'planificacion-[1-9][0-9]*\.json', p.name)]
    if not paths:
        return None
    source = max(paths, key=lambda p: int(p.stem.split('-')[1]))
    h = schemas.validate_schema(read(KIT / 'docs/plantillas/handoff.schema.json'), read(source))
    if h['identity']['change'] != change:
        raise ValueError('HANDOFF_IDENTITY_MISMATCH')
    if 'management' in h['context']:
        from contexto import validate_logical
        validate_logical(project, h['context']['management'])
    context = git_adapter.handoff_context(h)
    history = {}
    for prior in parent.glob('*.json'):
        if re.fullmatch(git_adapter.PHASE_PATTERN + r'-[1-9][0-9]*\.json', prior.name):
            data = schemas.validate_schema(read(KIT / 'docs/plantillas/handoff.schema.json'), read(prior))
            if data['identity']['change'] != change:
                raise ValueError('HANDOFF_HISTORY_IDENTITY_MISMATCH')
            history[prior.relative_to(Path(root)).as_posix()] = file_hash(prior)
    return {'version': 'content-v2', 'change': change, 'context': context, 'history': history,
            'moves': h['scope']['moves'], 'sync': h['scope']['sync'], 'git_inputs': h['scope']['git_inputs']}


def make_plan(root, policy_path, settings_path, base, criteria, projection=None, change=None, attempt=None, revalidating=False):
    policy, settings = load(policy_path, settings_path)
    resolution = None
    if 'attempt_templates' in settings:
        # Metadata Git plus pure selection; neither stage imports a client suite.
        raw = git_adapter.collect(root, base, [])
        preliminary = contract.build_plan(root, policy, raw['changes'], raw['base_sha'], criteria)
        policy, settings, resolution = attempts.resolve(root, policy, settings, change, attempt,
                                                       {c['check_id'] for c in preliminary['selected']})
    project_path = Path(root) / 'docs/proyecto.json'
    project = schemas.validate('project', read(project_path)) if project_path.is_file() else None
    projection = projection or projection_for(root, project, settings)
    if projection and 'history' not in projection:
        # Freeze existing contracts once, never future hashes or a growing list.
        projection = {**projection, 'history': {}}
        parent = Path(root) / 'docs/hu' / projection['change'] / 'handoffs'
        import re
        for path in parent.glob('*.json'):
            if re.fullmatch(git_adapter.PHASE_PATTERN + r'-[1-9][0-9]*\.json', path.name):
                projection['history'][path.relative_to(Path(root)).as_posix()] = file_hash(path)
    receipt = (git_adapter.content_view(root, base, settings['outputs'], projection,
                                      [p for c in policy['checks'] for p in c['inputs']])
               if projection else git_adapter.collect(root, base, settings['outputs']))
    provenance = {'git_input_digest': receipt['input_digest'], 'execution_digest': digest(settings),
                  'adapter_digest': adapter_digest(bool(project and project.get('context_management', {}).get('enabled'))), 'project_digest': digest(project)}
    if projection:
        provenance['projection'] = projection
    required = project['validation']['required_checks'] if project else []
    if resolution:
        # Required project checks participate even when no path/criterion selected them.
        original_policy, original_settings = load(policy_path, settings_path)
        selection = contract.build_plan(root, original_policy, receipt['changes'], receipt['base_sha'], criteria, required_check_ids=required)
        policy, settings, resolution = attempts.resolve(root, original_policy, original_settings, change, attempt,
                                                       {c['check_id'] for c in selection['selected']})
        receipt = (git_adapter.content_view(root, base, settings['outputs'], projection,
                       [p for c in policy['checks'] for p in c['inputs']]) if projection else git_adapter.collect(root, base, settings['outputs']))
        provenance['git_input_digest'] = receipt['input_digest']
        provenance['execution_digest'] = digest(settings)
        provenance['execution_resolution'] = resolution
    if 'lifecycle' in policy:
        selection = contract.build_plan(root, policy, receipt['changes'], receipt['base_sha'], criteria, required_check_ids=required)
        obligations = catalog.expected(policy, [c['check_id'] for c in selection['selected']])
        for name, expectation in (projection or {}).get('context', {}).get('test_inventory_expected', {}).items():
            if name not in obligations: raise ValueError('EXPECTED_TEST_CHECK_NOT_SELECTED')
            for key in ('files','nodeids','complete_files'):
                obligations[name][key] = sorted(set(obligations[name][key]+expectation[key]))
        provenance['test_inventory'] = {'schema_version':'1.0','expected':obligations}
        reconciled = catalog.reconcile(root, policy, base, settings['outputs'],(projection or {}).get('moves',[]))
        for row in reconciled['rows']:
            if row['git_status'] == 'D': continue
            for name in row['check_ids']:
                if name in obligations:
                    obligations[name]['files'] = sorted(set(obligations[name]['files'] + [row['path']]))
        if any(set(row['check_ids']).intersection(required) for row in policy['lifecycle']['test_inventory'] if row['state']=='retired'):
            raise ValueError('RETIRED_CHECK_STILL_REQUIRED')

    plan = contract.build_plan(root, policy, receipt['changes'], receipt['base_sha'], criteria, provenance, required)
    if projection and any(c['check_id'] not in projection['git_inputs'] for c in plan['selected']):
        raise ValueError('GIT_INPUTS_DECLARATION_REQUIRED: use [] only after reviewing independence')
    if project and not project['project']['setup_complete']:
        raise ValueError('PROJECT_SETUP_INCOMPLETE')
    if resolution and not revalidating and any(safe_path(root,name).exists() for name in settings['outputs']):
        raise ValueError('ATTEMPT_ALREADY_EXISTS_USE_NEW_PLAN_AND_OUTPUT_PATHS')
    schemas.validate('plan', plan)
    return plan


def resolved_settings(root, policy_path, settings_path, plan):
    policy, settings = load(policy_path, settings_path)
    identity = plan.get('provenance', {}).get('execution_resolution')
    if identity:
        policy, settings, observed = attempts.resolve(root, policy, settings, identity['change'], identity['attempt'], {c['check_id'] for c in plan['selected']})
        if observed != identity: raise ValueError('EXECUTION_RESOLUTION_CHANGED')
    return policy, settings


def current(root, policy_path, settings_path, plan):
    schemas.validate('plan', plan)
    # A historical plan must never silently adopt the new projection.
    projection = plan.get('provenance', {}).get('projection')
    if not projection and not plan.get('provenance', {}).get('execution_resolution') and 'lifecycle' not in read(policy_path):
        policy, settings = load(policy_path, settings_path)
        receipt = git_adapter.collect(root, plan['base_ref'], settings['outputs'])
        project_path = Path(root) / 'docs/proyecto.json'
        project = schemas.validate('project', read(project_path)) if project_path.is_file() else None
        provenance = {'git_input_digest': receipt['input_digest'], 'execution_digest': digest(settings),
                      'adapter_digest': adapter_digest(bool(project and project.get('context_management', {}).get('enabled'))), 'project_digest': digest(project)}
        rebuilt = contract.build_plan(root, policy, receipt['changes'], receipt['base_sha'],
                                      plan['required_criteria'], provenance,
                                      project['validation']['required_checks'] if project else [])
        return rebuilt == plan
    identity = plan.get('provenance', {}).get('execution_resolution', {})
    return make_plan(root, policy_path, settings_path, plan['base_ref'], plan['required_criteria'], projection, identity.get('change'), identity.get('attempt'), revalidating=True) == plan


def environment(settings):
    python = Path(settings['python_executable'] or '')
    if not python.is_absolute() or not python.is_file():
        raise ValueError('INTERPRETER_NOT_CONFIGURED')
    # Include the environment installation, not only the executable launcher.
    prefix = python.parent.parent
    metadata = {}
    for site in (prefix / 'Lib/site-packages', prefix / 'lib'):
        if site.exists():
            for entry in sorted(site.rglob('*.dist-info/METADATA')):
                metadata[entry.relative_to(prefix).as_posix()] = file_hash(entry)
    return digest({'interpreter': file_hash(python), 'location': str(python.resolve()),
                   'platform': platform.platform(), 'packages': metadata})


def report_files(root, config, outputs):
    names = [config['junit_path']]
    if config['coverage_path']:
        names.append(config['coverage_path'])
    if config.get('inventory_path'):
        names.append(config['inventory_path'])
    if any(name not in outputs for name in names):
        raise ValueError('REPORT_NOT_DECLARED_AS_OUTPUT')
    return [safe_path(root, name) for name in names]


def summarize(root, check, config, expected=None):
    data = reports.junit(safe_path(root, config['junit_path']), config['assertion_tests'])
    coverage_data = None
    if config['coverage_path']:
        coverage_data = reports.coverage(safe_path(root, config['coverage_path']),
                                         config['coverage_files'], config['coverage_minimum'])
        data['assertions']['coverage.minimum'] = 'passed' if coverage_data['passed'] else 'failed'
    obligation = expected or {'files':[],'nodeids':[],'complete_files':[]}
    if config.get('inventory_path'):
        data['inventory'] = reports.inventory(safe_path(root, config['inventory_path']), safe_path(root, config['junit_path']), obligation)
    elif any(obligation.values()):
        raise ValueError('REQUIRED_TEST_INVENTORY_ADAPTER_MISSING')
    return data, coverage_data


def run(root, policy_path, settings_path, plan):
    source_policy, settings = load(policy_path, settings_path)
    policy = source_policy
    identity = plan.get('provenance', {}).get('execution_resolution')
    if identity:
        policy, settings, resolution = attempts.resolve(root, policy, settings, identity['change'], identity['attempt'], {x['check_id'] for x in plan['selected']})
        if resolution != identity: raise ValueError('EXECUTION_RESOLUTION_CHANGED')
    if not current(root, policy_path, settings_path, plan) or plan['status'] != 'ready':
        raise ValueError('STALE_OR_BLOCKED_PLAN')
    records = []
    catalog = {x['id']: x for x in policy['checks']}
    # Validate every write target before executing the first check; preserve attempts.
    for selected in plan['selected']:
        name = selected['check_id']
        if not all(c.isalnum() or c in '_-' for c in name):
            raise ValueError('CHECK_ID_NOT_PATH_SAFE')
        config = settings['checks'].get(name)
        if config:
            paths = report_files(root, config, settings['outputs'])
            parent = paths[0].parent
            paths += [parent / ('receipt-' + name + '.json'), parent / ('stdout-' + name + '.log'), parent / ('stderr-' + name + '.log')]
            if any(p.relative_to(Path(root).resolve()).as_posix() not in settings['outputs'] for p in paths):
                raise ValueError('UNDECLARED_EVIDENCE_OUTPUT')
            if any(p.exists() for p in paths):
                raise ValueError('ATTEMPT_ALREADY_EXISTS_USE_NEW_PLAN_AND_OUTPUT_PATHS')
    for selected in plan['selected']:
        name = selected['check_id']
        check = catalog[name]
        now = execution.utc()
        record = {'check_id': name, 'input_digest': selected['input_digest'], 'status': 'blocked',
                  'exit_code': None, 'collected': 0, 'executed': 0, 'failed': 0, 'skipped': 0,
                  'assertions': {}, 'evidence': [], 'started_at': now, 'finished_at': now,
                  'environment_id': 'unavailable', 'authorization_ref': None,
                  'reason': 'LOCAL_EXECUTION_NOT_STARTED'}
        config = settings['checks'].get(name)
        try:
            if check['environment'] != 'local' or check['effect'] != 'local_execution' or check['kind'] != 'pytest':
                raise ValueError('CAPABILITY_INACTIVE_REQUIRES_AUTHORIZED_ADAPTER')
            if settings['reviewed_policy_digest'] != digest(source_policy):
                raise ValueError('CATALOG_NOT_REVIEWED')
            if not config:
                raise ValueError('CHECK_REPORT_ADAPTER_NOT_CONFIGURED')
            if set(check['required_assertions']) - set(config['assertion_tests']) - {'coverage.minimum'}:
                raise ValueError('ASSERTION_TEST_MAPPING_MISSING')
            if 'coverage.minimum' in check['required_assertions'] and not config['coverage_path']:
                raise ValueError('COVERAGE_REPORT_REQUIRED')
            record['environment_id'] = environment(settings)
            files = report_files(root, config, settings['outputs'])
            for p in files:
                p.parent.mkdir(parents=True, exist_ok=True)
            outcome = execution.run_process(root, check['argv'], settings['python_executable'], check['timeout_seconds'])
            record.update({key: outcome[key] for key in ('exit_code', 'started_at', 'finished_at')})
            parent = files[0].parent
            for stream in ('stdout', 'stderr'):
                path = parent / (stream + '-' + name + '.log')
                path.write_text(outcome[stream], encoding='utf-8')
                files.append(path)
            detail, coverage_data = {}, None
            try:
                detail, coverage_data = summarize(root, check, config, plan.get('provenance', {}).get('test_inventory', {}).get('expected', {}).get(name))
                record.update({key: detail[key] for key in ('collected', 'executed', 'failed', 'skipped', 'assertions')})
                passed = (outcome['exit_code'] == 0 and not outcome['timed_out']
                          and record['executed'] >= check['min_tests'] and record['skipped'] == 0
                          and record['failed'] == 0
                          and all(record['assertions'].get(a) == 'passed' for a in check['required_assertions']))
                record['status'] = 'passed' if passed else 'failed'
                record['reason'] = 'STRUCTURED_LOCAL_REPORT' if passed else 'SUITE_OR_ASSERTION_FAILED'
            except (ValueError, OSError, KeyError, TypeError):
                record['reason'] = 'MISSING_OR_INVALID_STRUCTURED_REPORT'
            receipt = {'schema_version': '1.0', 'plan_id': plan['plan_id'],
                       'candidate_digest': plan['candidate_digest'], 'check_id': name,
                       'input_digest': selected['input_digest'], 'environment_id': record['environment_id'],
                       'process': {k: v for k, v in outcome.items() if k not in ('stdout', 'stderr')},
                       'report': detail, 'coverage': coverage_data,
                       'files': [{'path': f.relative_to(Path(root).resolve()).as_posix(), 'sha256': file_hash(f)}
                                 for f in files if f.is_file()]}
            receipt_path = parent / ('receipt-' + name + '.json')
            write(receipt_path, receipt)
            record['evidence'] = receipt['files'] + [{'path': receipt_path.relative_to(Path(root).resolve()).as_posix(),
                                                      'sha256': file_hash(receipt_path)}]
        except (ValueError, OSError) as exc:
            record['reason'] = str(exc) if isinstance(exc, ValueError) else 'LOCAL_PROCESS_IO_ERROR'
        records.append(record)
    result = {'schema_version': '1.0', 'plan_id': plan['plan_id'],
              'candidate_digest': plan['candidate_digest'], 'records': records}
    schemas.validate('results', result)
    return result


def gate(root, policy_path, settings_path, plan, result):
    source_policy, settings = load(policy_path, settings_path)
    policy = source_policy
    identity = plan.get('provenance', {}).get('execution_resolution')
    if identity:
        policy, settings, resolution = attempts.resolve(root, policy, settings, identity['change'], identity['attempt'], {x['check_id'] for x in plan['selected']})
        if resolution != identity: raise ValueError('EXECUTION_RESOLUTION_CHANGED')
    schemas.validate('plan', plan)
    schemas.validate('results', result)
    verdict = contract.evaluate(root, policy, plan, result)
    blockers = list(verdict['blockers'])
    try:
        unchanged = current(root, policy_path, settings_path, plan)
    except (ValueError, OSError):
        unchanged = False
        blockers.append('CANDIDATE_REVALIDATION_FAILED')
    if not unchanged:
        blockers.append('GIT_OR_CONFIGURATION_CHANGED')
    catalog = {x['id']: x for x in policy['checks']}
    for record in result['records']:
        name = record['check_id']
        try:
            check, config = catalog[name], settings['checks'][name]
            if check['kind'] != 'pytest' or check['environment'] != 'local' or check['effect'] != 'local_execution':
                raise ValueError('CAPABILITY_INACTIVE')
            if record['environment_id'] != environment(settings):
                raise ValueError('ENVIRONMENT_CHANGED')
            finish = datetime.fromisoformat(record['finished_at'].replace('Z', '+00:00'))
            age = (datetime.now(timezone.utc) - finish).total_seconds()
            if not 0 <= age <= settings['max_evidence_age_seconds']:
                raise ValueError('EVIDENCE_EXPIRED_OR_FUTURE')
            receipt_path = safe_path(root, config['junit_path']).parent / ('receipt-' + name + '.json')
            receipt = read(receipt_path)
            for key in ('plan_id', 'candidate_digest'):
                if receipt[key] != plan[key]:
                    raise ValueError('FOREIGN_RECEIPT')
            for key in ('check_id', 'input_digest', 'environment_id'):
                if receipt[key] != record[key]:
                    raise ValueError('RECEIPT_RECORD_MISMATCH')
            if receipt['process']['argv'] != check['argv'] or receipt['process']['timed_out']:
                raise ValueError('PROCESS_RECEIPT_INVALID')
            for key in ('started_at', 'finished_at', 'exit_code'):
                if receipt['process'][key] != record[key]:
                    raise ValueError('PROCESS_RECORD_MISMATCH')
            detail, cov = summarize(root, check, config, plan.get('provenance', {}).get('test_inventory', {}).get('expected', {}).get(name))
            if detail != receipt['report'] or cov != receipt['coverage']:
                raise ValueError('STRUCTURED_REPORT_CHANGED')
            for key in ('collected', 'executed', 'failed', 'skipped', 'assertions'):
                if detail[key] != record[key]:
                    raise ValueError('REPORT_RECORD_MISMATCH')
            expected = receipt['files'] + [{'path': receipt_path.relative_to(Path(root).resolve()).as_posix(),
                                            'sha256': file_hash(receipt_path)}]
            if expected != record['evidence']:
                raise ValueError('PRIMARY_EVIDENCE_MISMATCH')
        except (KeyError, ValueError, TypeError, OSError):
            blockers.append('INVALID_OR_UNAVAILABLE_LOCAL_RECEIPT: ' + name)
    verdict['blockers'] = sorted(set(blockers))
    verdict['status'] = 'blocked' if blockers else 'passed'
    return verdict
