import importlib
import json

import pytest

from harness_core.configuration import ConfigError, load_document
from harness_core.contracts import Policy
from test_setup_contracts import module, scope


def service():
    assert importlib.util.find_spec('harness_local.access_scope') is not None, 'scoped adapter missing'
    return importlib.import_module('harness_local.access_scope')


def test_intersection_deny_and_explicit_directory_prefix(client):
    m=module()
    assert hasattr(m, 'authorize_access'), 'access evaluator missing'
    a=m.AccessScope.model_validate(scope())
    p=load_document(client['policy'],Policy)
    assert m.authorize_access(a,p,'src/main.py','read',['src/'])=='src/main.py'
    assert m.authorize_access(a,p,'README.md','read',['README.md'])=='README.md'
    for path,operation in [('README.md','write'), ('src/private/key','read'),
        ('src/private/key','write'), ('src2/main.py','read'), ('other','read')]:
        with pytest.raises(ConfigError,match='access_denied'): m.authorize_access(a,p,path,operation,[path])
    with pytest.raises(ConfigError,match='access_denied'): m.authorize_access(a,p,'src/main.py','write',['README.md'])
    p=Policy.model_validate({**p.model_dump(),'read_only_paths':['src/']})
    with pytest.raises(ConfigError,match='access_denied'): m.authorize_access(a,p,'src/main.py','write',['src/'])
    p=Policy.model_validate({**p.model_dump(),'denied_paths':['src/']})
    with pytest.raises(ConfigError,match='access_denied'): m.authorize_access(a,p,'src/main.py','read',['src/'])


def test_adapter_rejects_before_effect_and_checks_alias(client):
    api=service()
    (client['target']/'src').mkdir()
    (client['target']/'src/main.py').write_bytes(b'before')
    p=load_document(client['policy'],Policy)
    a=module().AccessScope.model_validate(scope())
    with api.ScopedTree(client['target'],a,p,['src/', 'README.md']) as tree:
        assert tree.read('src/main.py')==b'before'
        with pytest.raises(ConfigError,match='access_denied'): tree.create('README.md',b'forbidden')
        with pytest.raises(ConfigError): tree.read('SRC/main.py')
        tree.create('src/new.py',b'after')
    assert not (client['target']/'README.md').exists()
    assert (client['target']/'src/new.py').read_bytes()==b'after'


@pytest.mark.parametrize('path',['../policy.json','src/a:stream','src/NUL','src/main.py.', 'src/main.py ', 'src\\main.py'])
def test_adapter_invalid_paths_have_no_effect(client,path):
    api=service()
    with api.ScopedTree(client['target'], module().AccessScope.model_validate(scope()),load_document(client['policy'],Policy),['src/']) as tree:
        with pytest.raises(ConfigError): tree.create(path,b'forbidden')
    assert sorted(p.name for p in client['target'].iterdir())==['.git','.harness']


def test_junction_rejected_and_external_resource_preserved(client,scratch):
    import subprocess
    api=service()
    outside=scratch/'outside'; outside.mkdir(); (outside/'data').write_bytes(b'private')
    link=client['target']/'src'
    subprocess.run(['cmd','/c','mklink','/J',str(link),str(outside)],check=True,capture_output=True)
    with api.ScopedTree(client['target'],module().AccessScope.model_validate(scope()),load_document(client['policy'],Policy),['src/']) as tree:
        with pytest.raises(ConfigError): tree.read('src/data')
        with pytest.raises(ConfigError): tree.create('src/new',b'forbidden')
    assert (outside/'data').read_bytes()==b'private'
    assert not (outside/'new').exists()
def test_handle_read_preserves_chunks_and_rejects_oversize(scratch):
    from harness_core.configuration import ConfigError
    from harness_local.windows_fs import PinnedTree
    import pytest
    content=bytes(range(256))*400
    (scratch/'binary.bin').write_bytes(content)
    with PinnedTree(scratch) as tree:
        with tree.file('binary.bin') as handle:
            assert handle.read(1024*1024*1024)==content
        with tree.file('binary.bin') as handle:
            with pytest.raises(ConfigError,match='document_too_large'): handle.read(len(content)-1)
