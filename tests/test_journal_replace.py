import json

import pytest

from harness_local import execution_state


class Journal:
    def __init__(self,value): self.value=value
    def model_dump(self): return {'value':self.value}


def denied():
    error=PermissionError('Windows replacement denied')
    error.winerror=5
    return error


def test_atomic_journal_retries_transient_windows_denial(scratch,monkeypatch):
    path=scratch/'journal.json'
    execution_state.persist(path,Journal('old'))
    replace=execution_state.os.replace
    calls=[]
    def transient(source,destination):
        calls.append((source,destination))
        assert json.loads(path.read_bytes())=={'value':'old'}
        if len(calls)==1: raise denied()
        return replace(source,destination)
    monkeypatch.setattr(execution_state.os,'replace',transient)
    execution_state.persist(path,Journal('new'))
    assert len(calls)==2 and calls[0]==calls[1]
    assert json.loads(path.read_bytes())=={'value':'new'}


def test_atomic_journal_denial_is_bounded_and_preserves_previous(scratch,monkeypatch):
    path=scratch/'journal.json'
    execution_state.persist(path,Journal('old'))
    calls=[]
    def permanent(*args):
        calls.append(args)
        raise denied()
    monkeypatch.setattr(execution_state.os,'replace',permanent)
    with pytest.raises(PermissionError): execution_state.persist(path,Journal('new'))
    assert 1<len(calls)<=6
    assert json.loads(path.read_bytes())=={'value':'old'}
