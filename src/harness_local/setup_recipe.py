"""Freeze every conditional managed write before a checkout can be cloned."""
from importlib.resources import files
from pathlib import Path

from harness_core.configuration import ConfigError
from harness_core.onboarding_plan import canonical,sha
from .resources import kit
from .guided_resources import resources
from .guided_onboarding import serialized,context_content,tool_path
from .desktop_resources import render_integration


def recipe(inputs):
    r=inputs.guided_request
    base,_=kit()
    prepare={}
    for path,content in base.items():
        destination=inputs.descriptor.openspec_root+'/config.yaml' if path=='openspec/config.yaml' else path
        prepare[destination]=content
    prepare.update({'.harness/client.yaml':serialized(inputs.descriptor.model_dump()),
        'AGENTS.md':files('harness_local').joinpath('templates/AGENTS.md').read_text(encoding='utf-8'),
        '.harness/development.yaml':serialized(r.development.model_dump()),
        '.harness/context.md':context_content(r.development),
        '.agents/skills/harness-client-onboarding/SKILL.md':resources()['harness-client-onboarding/SKILL.md']})
    integrate=render_integration(r.catalog)
    integrate['AGENTS.md']=prepare['AGENTS.md']+'\n\n'+integrate['AGENTS.md']
    external={str(Path(r.binding_path).with_name(Path(r.binding_path).name+'.tools.json')):serialized(r.tool_binding.model_dump())}
    if r.binding_mode=='proposed': external[r.binding_path]=serialized(inputs.binding.model_dump())
    return dict(prepare=prepare,integrate=integrate,external=external)


def verify(frozen,child):
    for operation in child.preparation.operations:
        expected=frozen['prepare' if operation.scope=='target' else 'external'].get(operation.path)
        if expected is None or operation.content!=expected: raise ConfigError('plan_stale')
    for edit in child.integration_edits:
        if edit.content!=frozen['integrate'].get(edit.path): raise ConfigError('plan_stale')
