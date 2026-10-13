import json
import sys
from types import SimpleNamespace

import pytest

from test_validation import plan,request,api


def test_sql_parser_error_is_failed_sanitized_evidence(monkeypatch):
    from harness_local.validation import static_check
    class SqlglotError(Exception): pass
    def parse(*args,**kwargs): raise SqlglotError('SELECT customer-private-content')
    monkeypatch.setitem(sys.modules,'sqlglot',SimpleNamespace(parse=parse,errors=SimpleNamespace(SqlglotError=SqlglotError)))
    p=plan('sql'); e=static_check(p,request(p),b'SELECT invalid',filename='file.sql')
    assert e.status=='failed' and e.reason=='sql_parse_failed'
    assert 'customer-private-content' not in json.dumps(e.model_dump())


def test_scope_cannot_substitute_offline_for_worker():
    p=plan(); records=[]
    for t in p.tests:
        records.append(api().make_evidence(request(p,t.test_id),'passed',scope='offline-syntax',result={},observed=True))
    assert api().validation_gate(p,records)['status']=='blocked'


def test_remote_source_must_match_request_before_network(scratch):
    from test_validation_remote import ServiceDouble,target
    from harness_local.validation_remote import RemoteValidator
    p=plan('sql'); r=request(p,'sql-semantic',source_sha256='0'*64)
    s=ServiceDouble()
    result=RemoteValidator(scratch/'v.sqlite',s).run(p,r,target(),mode='sql',expected={},source='pass')
    assert result.reason=='source_hash_mismatch' and s.calls==[]


def test_static_source_hash_mismatch_blocks():
    from harness_local.validation import static_check
    p=plan(); r=request(p,source_sha256='0'*64)
    assert static_check(p,r,b'pass',filename='x.py').reason=='source_hash_mismatch'


def test_performance_cannot_pass_without_reproducible_baseline():
    p=plan(impacts=['performance'],performance_baseline_sha256='e'*64)
    records=[api().make_evidence(request(p,t.test_id),'passed',scope=t.scope,result={},observed=True) for t in p.tests]
    assert api().validation_gate(p,records)['status']=='blocked'
