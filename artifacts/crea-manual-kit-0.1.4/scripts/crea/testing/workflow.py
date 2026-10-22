"""Acciones separadas plan/run/gate. Planificar nunca ejecuta suites."""
from datetime import datetime, timezone
from fnmatch import fnmatchcase
from pathlib import Path
import platform

from . import execution, git_adapter, reports, schemas
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


def adapter_digest():
    paths = sorted((KIT / 'scripts/crea/testing').glob('*.py'))
    paths += sorted(ASSETS.glob('*.schema.json'))
    paths += [ASSETS.parent / 'scripts/contract.py', KIT / 'scripts/crea/pruebas.py']
    return digest({p.relative_to(KIT).as_posix(): file_hash(p) for p in paths})


def make_plan(root, policy_path, settings_path, base, criteria):
    policy, settings = load(policy_path, settings_path)
    receipt = git_adapter.collect(root, base, settings['outputs'])
    project_path = Path(root) / 'docs/proyecto.json'
    project = schemas.validate('project', read(project_path)) if project_path.is_file() else None
    provenance = {'git_input_digest': receipt['input_digest'], 'execution_digest': digest(settings),
                  'adapter_digest': adapter_digest(), 'project_digest': digest(project)}
    required = project['validation']['required_checks'] if project else []
    plan = contract.build_plan(root, policy, receipt['changes'], receipt['base_sha'], criteria, provenance, required)
    if project and not project['project']['setup_complete']:
        raise ValueError('PROJECT_SETUP_INCOMPLETE')
    schemas.validate('plan', plan)
    return plan


def current(root, policy_path, settings_path, plan):
    schemas.validate('plan', plan)
    return make_plan(root, policy_path, settings_path, plan['base_ref'], plan['required_criteria']) == plan


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
    if any(name not in outputs for name in names):
        raise ValueError('REPORT_NOT_DECLARED_AS_OUTPUT')
    return [safe_path(root, name) for name in names]


def summarize(root, check, config):
    data = reports.junit(safe_path(root, config['junit_path']), config['assertion_tests'])
    coverage_data = None
    if config['coverage_path']:
        coverage_data = reports.coverage(safe_path(root, config['coverage_path']),
                                         config['coverage_files'], config['coverage_minimum'])
        data['assertions']['coverage.minimum'] = 'passed' if coverage_data['passed'] else 'failed'
    return data, coverage_data


def run(root, policy_path, settings_path, plan):
    policy, settings = load(policy_path, settings_path)
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
            if settings['reviewed_policy_digest'] != digest(policy):
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
                detail, coverage_data = summarize(root, check, config)
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
    policy, settings = load(policy_path, settings_path)
    schemas.validate('plan', plan)
    schemas.validate('results', result)
    verdict = contract.evaluate(root, policy, plan, result)
    blockers = list(verdict['blockers'])
    if not current(root, policy_path, settings_path, plan):
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
            detail, cov = summarize(root, check, config)
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
