"""Passive packaged roles and procedures; loading does not activate Codex."""
import json
from importlib.resources import files
import tomllib

from harness_core.configuration import ConfigError, pairs, reject_secrets
from harness_core.desktop import RoleCatalog
from harness_core.onboarding_plan import canonical, sha, destination_path
from .quality_resources import load_quality


def resources():
    root = files('harness_local').joinpath('desktop_kit')
    try:
        manifest = json.loads(root.joinpath('manifest.json').read_bytes(), object_pairs_hook=pairs)
        if set(manifest) != {'schema_version', 'files'} or manifest['schema_version'] != 1:
            raise ValueError('manifest')
        result = {}
        for name, expected in manifest['files'].items():
            destination_path(name)
            raw = root.joinpath(name).read_bytes()
            if len(raw) > 128 * 1024 or sha(raw) != expected:
                raise ValueError('resource integrity')
            result[name] = raw.decode('utf-8')
        return result
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        raise ConfigError('desktop_resources_invalid') from None


def resource_digest():
    return sha(canonical(resources()))


def load_desktop():
    bundle = resources()
    try:
        value = json.loads(bundle['roles.json'], object_pairs_hook=pairs)
        reject_secrets(value)
        catalog = RoleCatalog.model_validate(value)
        practices = load_quality().practices
        ids = {r.id for r in practices.rules}
        if catalog.practice_pack_version != practices.version:
            raise ValueError('practice version')
        for role in catalog.roles:
            if not set(role.practice_ids) <= ids:
                raise ValueError('practice reference')
            bundle['agents/' + role.id + '.md']
        bundle['harness-hu/SKILL.md']
        bundle['AGENTS.md']
        return catalog
    except (ValueError, KeyError):
        raise ConfigError('desktop_resources_invalid') from None


def render_integration(catalog):
    bundle = resources()
    base = load_desktop()
    # A selected model is the only customization of the shipped responsibility.
    for role, original in zip(catalog.roles, base.roles, strict=True):
        if role.model_dump(exclude={'activated', 'model', 'effort'}) != original.model_dump(exclude={'activated', 'model', 'effort'}):
            raise ConfigError('catalog_contract_mismatch')
    active = [r for r in catalog.roles if r.activated]
    if not active:
        raise ConfigError('invalid_role_selection')
    content = {'AGENTS.md': bundle['AGENTS.md'], '.agents/skills/harness-hu/SKILL.md': bundle['harness-hu/SKILL.md']}
    config = []
    for role in active:
        path = '.codex/agents/harness-' + role.id + '.toml'
        # JSON quoting is also valid for these simple TOML string values.
        q = json.dumps
        instructions = bundle['agents/' + role.id + '.md']
        content[path] = (f'name = {q("harness-" + role.id)}\ndescription = {q(role.responsibility, ensure_ascii=False)}\n'
            f'model = {q(role.model)}\nmodel_reasoning_effort = {q(role.effort)}\n'
            f'sandbox_mode = {q(role.sandbox)}\ndeveloper_instructions = {q(instructions, ensure_ascii=False)}\n')
        config.append(f'[agents.harness-{role.id}]\ndescription = {q(role.responsibility, ensure_ascii=False)}\n'
                      f'config_file = {q("agents/harness-" + role.id + ".toml")}\n')
        tomllib.loads(content[path])
    content['.codex/config.toml'] = '\n'.join(config)
    tomllib.loads(content['.codex/config.toml'])
    return content
