"""Rejecting malformed setup payloads protects approval and client identity."""
import importlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError


def module():
    assert importlib.util.find_spec('harness_core.setup') is not None, 'setup contracts missing'
    return importlib.import_module('harness_core.setup')


def scope():
    return dict(schema_version=1, client_id='alpha', policy_sha256='a'*64,
                read_allow=['src/', 'README.md'], write_allow=['src/'], deny=['src/private/'])


def inputs(client):
    from harness_core.configuration import load_document
    return dict(schema_version=1, descriptor=load_document(client['target']/'.harness/client.yaml'),
                policy=load_document(client['policy']), binding=load_document(client['binding']),
                repository_url=client['origin'], access_scope={**scope(), 'policy_sha256': json.loads(client['binding'].read_text())['policy_sha256']},
                capabilities=['local'], sources={'descriptor':'file', 'policy':'file', 'binding':'local', 'access_scope':'user'})


def test_contracts_roundtrip_and_schema_snapshots(client, scratch):
    m=module()
    value=m.SetupInput.model_validate(inputs(client))
    assert value.descriptor.repository=='demo/alpha'
    assert m.SetupInput.model_validate_json(value.model_dump_json())==value
    installed=dict(schema_version=1, version='0.1.0', product_sha256='b'*64,
        installation_root=str(scratch/'runtime'), runtime_path=str(scratch/'runtime/python.exe'),
        skill_path=str(scratch/'skills/harness-setup/SKILL.md'), tools=[],
        owned_files={'python.exe':'c'*64}, resource_installed=False, skill_discovered=False)
    record=m.InstallationRecord.model_validate(installed)
    assert record.certified is False and record.release_allowed is False
    report=m.SetupReport(schema_version=1, client_id='alpha', checkout_id='checkout', plan_sha256='d'*64,
        prepared=True, stages=[], capabilities=[dict(schema_version=1, id='desktop', status='not_checked',
            reason='skill_discovery_pending', next_action='Comprobar descubrimiento en Codex', evidence=[])])
    assert report.prepared and not report.certified and not report.publication_allowed
    for model, obj in [(m.AccessScope, value.access_scope), (m.SetupInput,value), (m.InstallationRecord,record), (m.SetupReport,report)]:
        assert model.model_validate_json(obj.model_dump_json())==obj
        with pytest.raises(ValidationError): model.model_validate({**obj.model_dump(), 'unknown':True})
    for model in m.MODELS:
        for root in ('schemas', 'src/harness_core/schemas'):
            assert json.loads(Path(root,model.__name__.lower()+'.schema.json').read_text())==model.model_json_schema()


@pytest.mark.parametrize('field,value', [('repository_url','https://github.com/demo/other.git'),
    ('repository_url','https://user:pass@github.com/demo/alpha.git'), ('capabilities',['arbitrary'])])
def test_setup_rejects_identity_url_and_unknown_capability(client,field,value):
    with pytest.raises(ValidationError): module().SetupInput.model_validate({**inputs(client),field:value})


def test_scope_identity_policy_and_foreign_binding_rejected(client):
    m=module()
    data=inputs(client)
    for scope_field, value in [('client_id','beta'), ('policy_sha256','f'*64)]:
        with pytest.raises(ValidationError): m.SetupInput.model_validate({**data,'access_scope':{**data['access_scope'],scope_field:value}})
    with pytest.raises(ValidationError): m.SetupInput.model_validate({**data,'binding':{**data['binding'],'client_id':'beta'}})


def test_plan_integrity_and_approval_binding(client):
    from harness_core.onboarding_plan import canonical,sha
    m=module()
    data=dict(schema_version=1, kind='setup_plan', run_id='setup', inputs=m.SetupInput.model_validate(inputs(client)).model_dump(), input_hashes={},
        child_plans={}, child_payloads={}, setup_operations=[], stages=[], technical_reads=['.git/HEAD', '.harness/client.yaml'], integration_writes=[],
        effects=[], applicable=True, blockers=[])
    plan=m.SetupPlan.model_validate({**data,'plan_sha256':sha(canonical(data))})
    assert m.SetupPlan.model_validate_json(plan.model_dump_json())==plan
    with pytest.raises(ValidationError): m.SetupPlan.model_validate({**plan.model_dump(), 'technical_reads':['.git/config']})
    with pytest.raises(ValidationError): m.SetupPlan.model_validate({**data,'plan_sha256':'0'*64})


@pytest.mark.parametrize('path', ['../src/', 'C:/src/', 'src/a:stream', 'src/CON.txt', 'src/A.', 'src/a ', 'src//a', 'src\\a', 'src/*'])
def test_access_scope_rejects_windows_escapes(path):
    with pytest.raises(ValidationError): module().AccessScope.model_validate({**scope(),'read_allow':[path]})


def test_access_scope_rejects_case_aliases_and_empty_scope_is_closed():
    m=module()
    with pytest.raises(ValidationError): m.AccessScope.model_validate({**scope(),'read_allow':['src/', 'SRC/']})
    assert m.AccessScope.model_validate({**scope(),'read_allow':[], 'write_allow':[]}).read_allow==[]


def test_published_v1_schemas_unchanged():
    from harness_core.contracts import Descriptor,Policy,Binding
    for model in (Descriptor,Policy,Binding):
        # Existing published schemas retain their original shapes and validators.
        schema=json.loads(Path('schemas',model.__name__.lower()+'.schema.json').read_text())
        assert schema==model.model_json_schema()
