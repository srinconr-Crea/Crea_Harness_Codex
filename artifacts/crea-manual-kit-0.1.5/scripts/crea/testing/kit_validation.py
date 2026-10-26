"""Comprobación estructural offline; jamás ejecuta comandos del catálogo."""
from collections import Counter
from pathlib import Path
import re
import tomllib
import yaml

from .common import file_hash, read, safe_path
from .schemas import validate_schema

LOCAL_STATE = {'.git', '.venv', '__pycache__', '.test-work', '.pytest_cache'}


def files(root):
    return sorted(p for p in Path(root).rglob('*') if p.is_file()
                  and not set(p.relative_to(root).parts) & LOCAL_STATE)


def validate_kit(root, original=False, config_override=None):
    root = Path(root).resolve()
    config = config_override if config_override is not None else read(root / 'docs/proyecto.json')
    validate_schema(read(root / 'docs/proyecto.schema.json'), config)
    def required(name):
        path = safe_path(root, name)
        if not path.is_file():
            raise ValueError('REQUIRED_FILE_MISSING: ' + name)
        return path
    required(config['project']['context_path'])
    required(config['workflow']['orchestrator'])
    if config['workflow']['max_active_agents'] != 1 or not config['workflow']['require_manual_archive_approval'] or not config['workflow']['require_plan_approval']:
        raise ValueError('HUMAN_OR_SEQUENTIAL_POLICY_INVALID')
    registered = {}
    registered_paths = set()
    for skill in config['extensions']['skills']:
        name, path = skill['name'], skill['path']
        if name in registered or path in registered_paths or not path.startswith('.agents/skills/'):
            raise ValueError('DUPLICATE_OR_INVALID_SKILL_REGISTRATION')
        required(path)
        registered[name] = path
        registered_paths.add(path)
    discovered = {}
    for path in sorted((root / '.agents/skills').rglob('SKILL.md')):
        text = path.read_text(encoding='utf-8-sig')
        front = yaml.safe_load(text.split('---', 2)[1])
        name = front['name']
        if name in discovered:
            raise ValueError('DUPLICATE_SKILL_NAME')
        discovered[name] = path.relative_to(root).as_posix()
        if name in registered and discovered[name] != registered[name]:
            raise ValueError('SKILL_NAME_PATH_MISMATCH')
    for role, skills in config['workflow']['skills_by_role'].items():
        for name in skills:
            path = registered.get(name, '.agents/skills/' + name + '/SKILL.md')
            required(path)
            if discovered.get(name) != path:
                raise ValueError('ROLE_SKILL_NAME_MISMATCH')
    roles = {}
    for name, path in config['workflow']['roles'].items():
        profile = tomllib.loads(required(path).read_text(encoding='utf-8-sig'))
        if profile.get('name') != name or not all(profile.get(k) for k in ('description', 'model', 'model_reasoning_effort', 'developer_instructions')):
            raise ValueError('ROLE_PROFILE_INVALID')
        roles[name] = profile
    native = tomllib.loads(required('.codex/config.toml').read_text(encoding='utf-8-sig'))
    if native['agents']['max_concurrent_threads_per_session'] != 1:
        raise ValueError('NATIVE_THREAD_CAP_INVALID')
    for path in config['practices'].values():
        required(path)
    for item in config['inventory']['paths']:
        if item['exists'] and not safe_path(root, item['path'].rstrip('/')).exists():
            raise ValueError('DECLARED_INVENTORY_PATH_MISSING')
    testing = config['validation']['testing']
    assets = root / '.agents/skills/Crea/crea-pruebas/assets'
    checked = 0
    for kind, key in [('policy', 'policy_path'), ('execution', 'execution_path'), ('calibration', 'calibration_path'),
                      ('failure-modes', 'failure_modes_path'), ('history', 'history_path'), ('capabilities', 'capabilities_path')]:
        validate_schema(read(assets / (kind + '.schema.json')), read(required(testing[key])))
        checked += 1
    from .common import contract
    policy = contract.validate_policy(read(required(testing['policy_path'])))
    checks = {x['id'] for x in policy['checks']}
    if set(config['validation']['required_checks']) - checks:
        raise ValueError('REQUIRED_CHECK_REFERENCE_UNKNOWN')
    calibration = read(required(testing['calibration_path']))
    for rule in calibration['rules']:
        if rule['stage'] == 'block' and not rule['human_promotion_ref']:
            raise ValueError('BLOCK_RULE_WITHOUT_HUMAN_PROMOTION')
    for name, value in testing.items():
        if value and (name.endswith('_adapter') or name.endswith('_path')):
            required(value)
    for adapter in read(required(testing['capabilities_path']))['adapters'].values():
        if adapter['enabled']:
            required(adapter['path'])
        elif adapter['path'] is not None or not adapter['blocked_reason']:
            raise ValueError('INACTIVE_ADAPTER_MUST_BLOCK_EXPLICITLY')
    if config['project']['setup_complete'] and not policy['setup_complete']:
        raise ValueError('PROJECT_SETUP_WITHOUT_TEST_POLICY')
    schema_count = 0
    from jsonschema import Draft202012Validator
    for path in assets.glob('*.schema.json'):
        Draft202012Validator.check_schema(read(path))
        schema_count += 1
    handoff_schema = root / 'docs/plantillas/handoff.schema.json'
    if handoff_schema.exists():
        Draft202012Validator.check_schema(read(handoff_schema))
        required('scripts/crea/transiciones.py')
        required('docs/constituciones/README.md')
        schema_count += 1
    for path in assets.glob('*.template.json'):
        kind = path.name.removesuffix('.template.json')
        validate_schema(read(assets / (kind + '.schema.json')), read(path))
    links = 0
    own_paths = list((root / 'docs').rglob('*.md')) + list((root / '.agents/skills/Crea').rglob('*.md'))
    for path in own_paths:
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8-sig')):
            if '://' in target or target.startswith('#') or any(c in target for c in '<>{}'):
                continue
            target = target.split('#')[0]
            if target and not (path.parent / target).exists():
                raise ValueError('LOCAL_MARKDOWN_REFERENCE_MISSING: ' + path.relative_to(root).as_posix())
            links += 1
    manifest_count = 0
    if original:
        manifest = read(required('kit-manifest.json'))
        manifest_paths = set()
        for entry in manifest['files']:
            path = required(entry['path'])
            if entry['path'] in manifest_paths or file_hash(path) != entry['sha256'] or path.stat().st_size != entry['bytes']:
                raise ValueError('ORIGINAL_MANIFEST_MISMATCH')
            manifest_paths.add(entry['path'])
        actual = {p.relative_to(root).as_posix() for p in files(root)} - {'kit-manifest.json'}
        if actual != manifest_paths:
            raise ValueError('ORIGINAL_MANIFEST_FILESET_MISMATCH')
        manifest_count = len(manifest_paths)
    return {'status': 'passed', 'version': config['inventory'].get('observed_kit_version'),
            'roles': len(roles), 'skills': len(discovered), 'schemas': schema_count,
            'instances': checked, 'local_links': links, 'manifest_files': manifest_count,
            'setup_complete': config['project']['setup_complete'],
            'business_tests_executed': False, 'native_agents_executed': False}
