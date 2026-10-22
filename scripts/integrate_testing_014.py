"""Autoría local de contratos 0.1.4; no opera repositorios cliente."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / 'artifacts/crea-manual-kit-0.1.4'
ASSETS = KIT / '.agents/skills/Crea/crea-pruebas/assets'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def write(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def obj(properties, required=None):
    return {'type': 'object', 'properties': properties,
            'required': list(properties) if required is None else required, 'additionalProperties': False}


def arr(items):
    return {'type': 'array', 'items': items, 'uniqueItems': True}


def main():
    string = {'type': 'string', 'minLength': 1}
    nullable = {'type': ['string', 'null'], 'minLength': 1}
    sha = {'type': ['string', 'null'], 'pattern': '^[a-f0-9]{64}$'}
    check = obj({'junit_path': string, 'assertion_tests': {'type': 'object', 'additionalProperties':
                {'type': 'array', 'items': string, 'minItems': 1, 'uniqueItems': True}},
                 'coverage_path': nullable, 'coverage_files': arr(string),
                 'coverage_minimum': {'type': ['number', 'null'], 'minimum': 0, 'maximum': 100}})
    check['allOf'] = [{'if': {'properties': {'coverage_path': {'type': 'string'}}},
                      'then': {'properties': {'coverage_minimum': {'type': 'number'},
                                              'coverage_files': {'minItems': 1}}}}]
    execution_schema = obj({'schema_version': {'const': '1.0'}, 'python_executable': nullable,
                            'reviewed_policy_digest': sha, 'max_evidence_age_seconds': {'type': 'integer', 'minimum': 1},
                            'outputs': arr(string), 'checks': {'type': 'object', 'additionalProperties': check}})
    execution_schema['$schema'] = 'https://json-schema.org/draft/2020-12/schema'
    write(ASSETS / 'execution.schema.json', execution_schema)
    write(KIT / 'docs/pruebas/execution.json', {'schema_version': '1.0', 'python_executable': None,
          'reviewed_policy_digest': None, 'max_evidence_age_seconds': 3600, 'outputs': [], 'checks': {}})
    for kind, name in [('policy', 'policy'), ('calibration', 'calibration'), ('failure-modes', 'failure-modes'), ('history', 'review-history')]:
        write(KIT / ('docs/pruebas/' + name + '.json'), read(ASSETS / (kind + '.template.json')))
    schema = read(ASSETS / 'plan.schema.json')
    schema['properties']['provenance'] = obj({k: {'type': 'string', 'pattern': '^[a-f0-9]{64}$'}
        for k in ('git_input_digest', 'execution_digest', 'adapter_digest', 'project_digest')})
    schema['properties']['required_check_ids'] = arr(string)
    write(ASSETS / 'plan.schema.json', schema)
    caps = {'schema_version': '1.0', 'adapters': {}}
    for name, path in [('git', 'git_adapter.py'), ('execution', 'execution.py'), ('pytest_report', 'reports.py'), ('strict_schema', 'schemas.py')]:
        caps['adapters'][name] = {'enabled': True, 'path': 'scripts/crea/testing/' + path, 'blocked_reason': None}
    for name in ('runtime', 'spark_local', 'sast', 'mutation', 'reviewer_evals', 'cross_plan_reuse', 'ci'):
        caps['adapters'][name] = {'enabled': False, 'path': None,
            'blocked_reason': 'No adaptador certificado en 0.1.4; si es requerido, bloquear. Requiere integración específica autorizada.'}
    write(KIT / 'docs/pruebas/capabilities.json', caps)
    cap_props = {}
    for name, value in caps['adapters'].items():
        cap_props[name] = obj({'enabled': {'const': value['enabled']}, 'path': {'const': value['path']},
                              'blocked_reason': {'type': 'string', 'minLength': 1} if not value['enabled'] else {'const': None}})
    cap_schema = obj({'schema_version': {'const': '1.0'}, 'adapters': obj(cap_props)})
    cap_schema['$schema'] = execution_schema['$schema']
    write(ASSETS / 'capabilities.schema.json', cap_schema)
    config = read(KIT / 'docs/proyecto.json')
    config['workflow']['roles']['tester'] = '.codex/agents/tester.toml'
    for role in ('planner', 'developer', 'tester', 'reviewer'):
        values = config['workflow']['skills_by_role'].setdefault(role, [])
        if 'crea-pruebas' not in values:
            values.append('crea-pruebas')
    config['validation'] = {'required_checks': [], 'no_checks_policy': 'policy_before_apply',
        'runtime_policy': 'required_by_behavior_or_approved_client_policy',
        'testing': {'enabled': True, 'skill_path': '.agents/skills/Crea/crea-pruebas/SKILL.md',
                    'policy_path': 'docs/pruebas/policy.json', 'execution_path': 'docs/pruebas/execution.json',
                    'calibration_path': 'docs/pruebas/calibration.json', 'failure_modes_path': 'docs/pruebas/failure-modes.json',
                    'history_path': 'docs/pruebas/review-history.json', 'capabilities_path': 'docs/pruebas/capabilities.json',
                    'helper_path': '.agents/skills/Crea/crea-pruebas/scripts/contract.py',
                    'artifacts_pattern': 'docs/hu/{change}/pruebas/', 'strict_schema_validation': True,
                    'git_adapter': 'scripts/crea/testing/git_adapter.py', 'execution_adapter': 'scripts/crea/testing/execution.py',
                    'pytest_adapter': 'scripts/crea/testing/reports.py', 'workflow_adapter': 'scripts/crea/pruebas.py',
                    'cross_plan_reuse_adapter': None, 'runtime_adapter': None, 'ci_adapter': None}}
    for name, path, roles in [('crea-orquestador', '.agents/skills/Crea/orquestador/SKILL.md', ['principal']),
                             ('creating-databricks-agents', '.agents/skills/Crea/creating-databricks-agents/SKILL.md', ['developer']),
                             ('crea-pruebas', '.agents/skills/Crea/crea-pruebas/SKILL.md', ['planner', 'developer', 'tester', 'reviewer'])]:
        config['extensions']['skills'].append({'name': name, 'path': path, 'roles': roles, 'when': 'Según alcance de la tarea'})
    config['extensions']['agents'].append({'name': 'tester', 'path': '.codex/agents/tester.toml', 'when': 'Después de developer, antes de reviewer'})
    config['inventory']['observed_kit_version'] = '0.1.4'
    config['inventory']['observed_on'] = '2026-10-21'
    config['inventory']['paths'].append({'path': 'docs/pruebas/', 'purpose': 'Catálogo único, fallos, calibración y adaptadores', 'exists': True, 'owner': 'shared'})
    for row in config['inventory']['paths']:
        row['purpose'] = row['purpose'].replace('planner, developer, reviewer', 'planner, developer, tester, reviewer')
    write(KIT / 'docs/proyecto.json', config)
    schema = read(KIT / 'docs/proyecto.schema.json')
    schema['properties']['workflow']['properties']['roles'] = obj({r: string for r in ('planner', 'developer', 'tester', 'reviewer')})
    schema['properties']['validation'] = obj({
        'required_checks': arr(string), 'no_checks_policy': {'const': 'policy_before_apply'},
        'runtime_policy': {'const': 'required_by_behavior_or_approved_client_policy'},
        'testing': obj({key: ({'const': value} if isinstance(value, bool) or value is None or key == 'artifacts_pattern' else string)
                        for key, value in config['validation']['testing'].items()})})
    write(KIT / 'docs/proyecto.schema.json', schema)
    write(KIT / 'docs/pruebas/INTEGRACION.json', {'version': '0.1.4', 'source_package_version': '0.1.0',
          'skill_copy': 'Completa; agents/references/assets/scripts preservados.',
          'adaptations': ['contract.build_plan/evaluate aceptan procedencia opcional determinista',
                          'plan.schema incluye procedencia opcional', 'schemas execution/capabilities agregados',
                          'referencia de adaptadores locales añadida; upstream sin cambios']})


if __name__ == '__main__':
    main()
