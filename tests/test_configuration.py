import json
from pathlib import Path

import pytest

from harness_core.configuration import ConfigError, load_document, validate_configuration
from harness_core.contracts import Descriptor, Policy, Binding


def test_contracts_reject_unknown_version_and_fields():
    valid = dict(schema_version=1, client_id="alpha", repository="demo/alpha",
                 base_branch="develop", openspec_root="openspec")
    assert Descriptor.model_validate(valid).client_id == "alpha"
    for changed in [dict(valid, schema_version=2), dict(valid, permissions=["all"]),
                    dict(valid, openspec_root="../private"), dict(valid, base_branch="a..b")]:
        with pytest.raises(ValueError):
            Descriptor.model_validate(changed)


def test_validation_error_identifies_field_without_value(scratch):
    p=scratch/'descriptor.json'
    p.write_text('{"schema_version":2,"client_id":"alpha","repository":"demo/alpha","base_branch":"develop"}')
    with pytest.raises(ConfigError) as caught:
        load_document(p,Descriptor)
    assert caught.value.document=='Descriptor'
    assert 'schema_version' in caught.value.fields


def test_strict_version_rejects_bool():
    with pytest.raises(ValueError):
        Descriptor(schema_version=True,client_id='alpha',repository='demo/alpha',base_branch='develop')


def test_traversal_and_linked_ancestors(client):
    from harness_core.configuration import safe_path
    with pytest.raises(ConfigError,match='path_traversal'):
        safe_path(client['target']/'..'/'policy.json')
    link=client['target'].parent/'junction'
    import subprocess
    result=subprocess.run(['powershell','-NoProfile','-Command',
        'New-Item -ItemType Junction -Path $args[0] -Target $args[1]',str(link),str(client['target'])],capture_output=True)
    # Use quoted arguments if powershell -Command consumes positional arguments as expressions.
    if result.returncode:
        command="New-Item -ItemType Junction -Path '"+str(link).replace("'","''")+"' -Target '"+str(client['target']).replace("'","''")+"'"
        subprocess.run(['powershell','-NoProfile','-Command',command],check=True,capture_output=True)
    with pytest.raises(ConfigError,match='linked_path'):
        safe_path(link/'.harness/client.yaml')
    link.rmdir()  # Remove only junction, preserving its target.
    assert (client['target']/'.harness/client.yaml').is_file()


def test_yaml_aliases_cannot_expand(scratch):
    p=scratch/'aliases.yaml'
    p.write_text('a: &a [hello, hello]\nb: &b [*a,*a]\nc: [*b,*b]\n')
    with pytest.raises(ConfigError,match='yaml_alias_not_allowed'):
        load_document(p)


def test_documented_fixtures_validate():
    import hashlib
    for name in ('alpha','beta'):
        root=Path('tests/fixtures')/name
        descriptor=load_document(root/'descriptor.json',Descriptor)
        policy=load_document(root/'policy.json',Policy)
        binding=load_document(root/'binding.json',Binding)
        assert descriptor.client_id==policy.client_id==binding.client_id==name
        assert binding.policy_sha256==hashlib.sha256((root/'policy.json').read_bytes()).hexdigest()


@pytest.mark.parametrize('model,name',[(Descriptor,'descriptor'),(Policy,'policy'),(Binding,'binding')])
def test_all_contracts_are_strict(model,name):
    valid=json.loads((Path('tests/fixtures/alpha')/(name+'.json')).read_text())
    for data in (dict(valid,schema_version=2),dict(valid,unknown='value')):
        with pytest.raises(ValueError):
            model.model_validate(data)


@pytest.mark.parametrize('value',['private//','../x','/x','C:/x','a//b','a\\b'])
def test_repository_path_patterns_reject_invalid_values(value):
    from harness_core.contracts import relative
    with pytest.raises(ValueError):
        relative(value)


@pytest.mark.parametrize("body", ['{bad', 'schema_version: 1\nschema_version: 1',
                                 '{"a":1,"a":2}', 'password: SUPER_SECRET',
                                 'description: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456'])
def test_unsafe_documents_are_rejected(scratch, body):
    p = scratch / "input.yaml"
    p.write_text(body, encoding="utf-8")
    with pytest.raises(ConfigError) as caught:
        load_document(p, Descriptor)
    assert body not in str(caught.value)
    assert "SUPER_SECRET" not in str(caught.value)


def test_size_and_regular_file_limit(scratch):
    p = scratch / "large.yaml"
    p.write_bytes(b" " * (128 * 1024 + 1))
    with pytest.raises(ConfigError):
        load_document(p, Descriptor)
    with pytest.raises(ConfigError):
        load_document(scratch, Descriptor)


def test_valid_configuration_and_transport_aliases(client):
    for origin in ["https://github.com/demo/alpha.git", "git@github.com:demo/alpha.git",
                   "ssh://git@github.com/demo/alpha"]:
        result = validate_configuration(client["target"], client["policy"], client["binding"], origin)
        assert result["descriptor"].client_id == "alpha"


@pytest.mark.parametrize("origin,code", [(None,"origin_missing"),
    ("https://github.com/demo/other.git","repository_mismatch"),
    ("https://SECRET@github.com/demo/alpha.git","invalid_remote")])
def test_origin_rejection(client, origin, code):
    with pytest.raises(ConfigError) as caught:
        validate_configuration(client["target"],client["policy"],client["binding"],origin)
    assert caught.value.code == code
    assert "SECRET" not in str(caught.value)


def test_changed_policy_is_rejected(client):
    client["policy"].write_bytes(client["policy"].read_bytes()+b"\n")
    with pytest.raises(ConfigError, match="policy_hash_mismatch"):
        validate_configuration(client["target"],client["policy"],client["binding"],client["origin"])


@pytest.mark.parametrize("field,value,code", [
    ("client_id","beta","client_mismatch"),
    ("target_path","OTHER","target_mismatch"),
    ("state_dir","INSIDE","state_path_invalid")])
def test_cross_client_and_state_rejections(client, field, value, code):
    p=client["binding"]
    data=json.loads(p.read_text())
    data[field] = str(client["target"] / "alpha" / "checkout") if value=="INSIDE" else (
        str(client["target"].parent / "other") if value=="OTHER" else value)
    p.write_text(json.dumps(data))
    with pytest.raises(ConfigError) as caught:
        validate_configuration(client["target"],client["policy"],p,client["origin"])
    assert caught.value.code == code
