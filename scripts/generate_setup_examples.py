"""Generate synthetic, schema-validated setup inputs without customer data."""
import json
from pathlib import Path

from harness_core.desktop import activate_profiles
from harness_core.onboarding_plan import canonical, sha
from harness_core.setup import SetupInput
from harness_local.desktop_resources import load_desktop
from harness_local.environment_setup import interview


def main():
    folder=Path(__file__).resolve().parents[1]/'docs/examples/setup'
    folder.mkdir(parents=True,exist_ok=True)
    descriptor=dict(schema_version=1,client_id='demo',repository='example/demo',base_branch='main',openspec_root='openspec')
    policy=dict(schema_version=1,policy_id='demo',client_id='demo',repository='example/demo',base_branch='main',
        branch_prefix='feature/',read_only_paths=[],denied_paths=['private/'],max_files=40,max_bytes=2000000)
    binding=dict(schema_version=1,client_id='demo',checkout_id='checkout',target_path='C:/HarnessExamples/demo',
        policy_sha256=sha(canonical(policy)),state_dir='C:/HarnessExamples/state/demo/checkout')
    catalog=load_desktop()
    profiles={role.id:dict(model='synthetic-model',effort='medium') for role in catalog.roles}
    catalog=activate_profiles(catalog,profiles,{'synthetic-model':['medium']})
    development=dict(schema_version=1,client_id='demo',stack=['Python'],conventions=['pytest'],
        business_rules=['Regla de ejemplo; reemplazar por decisiones del cliente'],roles=list(profiles),validations=['pytest'],
        sources={key:'user' for key in ('stack','conventions','business_rules','roles','validations')})
    value=dict(schema_version=1,descriptor=descriptor,policy=policy,binding=binding,
        repository_url='https://github.com/example/demo.git',access_scope=dict(schema_version=1,client_id='demo',
            policy_sha256=binding['policy_sha256'],read_allow=['src/','tests/'],write_allow=['src/','tests/'],deny=['private/']),
        capabilities=['local','git','desktop'],sources={key:'template' for key in ('descriptor','policy','binding','repository_url','access_scope','capabilities')},
        guided_request=dict(schema_version=1,target_path=binding['target_path'],policy_path='C:/HarnessExamples/policy.json',
            binding_path='C:/HarnessExamples/binding.json',repository=descriptor['repository'],base_branch='main',
            catalog=catalog.model_dump(),development=development,tool_binding=dict(schema_version=1,client_id='demo',checkout_id='checkout',tools=[])))
    value=SetupInput.model_validate(value).model_dump()
    assert interview(value)['questions']==[]
    partial=dict(schema_version=1,descriptor=descriptor,sources={'descriptor':'template'})
    assert 'descriptor' not in {question['field'] for question in interview(partial)['questions']}
    for name,content in (('complete.json',value),('partial.json',partial),('policy.json',policy),('binding.json',binding)):
        (folder/name).write_bytes(canonical(content))
    print(json.dumps({'examples':4,'complete':'ready','partial':'blocked','synthetic':True}))


if __name__=='__main__': main()
