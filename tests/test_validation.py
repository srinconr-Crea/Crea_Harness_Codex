"""Candidate validation contracts, selection and honest coverage."""
import json
from pathlib import Path

import pytest
from pydantic import ValidationError


def api():
    from harness_core import validation
    return validation


def plan(technology='python', **updates):
    values = dict(client_id='alpha', run_id='run1', attempt=1, candidate_sha256='a'*64,
        plan_revision=1, technologies=[technology], impacts=['logic'])
    values.update(updates)
    from harness_local.validation import select_plan
    return select_plan(**values)


def request(p, test_id=None, **updates):
    import sys
    from harness_core.onboarding_plan import sha
    import harness_local.validation as static_module
    values = dict(schema_version=1, plan_sha256=p.plan_sha256,
        test_id=test_id or p.tests[0].test_id, client_id=p.client_id, run_id=p.run_id,
        attempt=p.attempt, candidate_sha256=p.candidate_sha256, plan_revision=p.plan_revision,
        practice_pack_sha256=p.practice_pack_sha256, data_sha256='b'*64,
        runtime='python-3.13', runtime_sha256=sha(sys.version.encode()), tool_sha256=sha(Path(static_module.__file__).read_bytes()),
        request_key='request1', command=['harness','validate','static'])
    values.update(updates)
    return api().ValidationRequest(**values)


def test_pure_python_selects_behavior_without_remote():
    p=plan()
    assert [(t.test_id,t.required,t.layer) for t in p.tests]==[('python-static',True,'L0'),('python-unit',True,'L1')]
    assert p.catalog_test_ids==['T05','T06']


@pytest.mark.parametrize('technology,impact,required',[
    ('sql','delta','delta-semantic'),('notebook','integration','notebook-integration'),
    ('pyspark','logic','spark-unit'),('yaml-dabs','integration','bundle-validate'),
    ('cicd','logic','cicd-static')])
def test_selection_never_replaces_semantics_with_parser(technology,impact,required):
    p=plan(technology,impacts=[impact])
    assert next(t for t in p.tests if t.test_id==required).required
    assert next(t for t in p.tests if t.test_id==required).layer != 'L0' or technology=='cicd'


def test_performance_is_advisory_without_baseline():
    p=plan(impacts=['performance'])
    assert not next(t for t in p.tests if t.test_id=='performance').required
    assert next(t for t in plan(impacts=['performance'],performance_baseline_sha256='e'*64).tests
        if t.test_id=='performance').required


def test_strict_contract_integrity_and_secrets():
    p=plan()
    for updates in ({'schema_version':2},{'extra':True},{'candidate_sha256':'bad'},
        {'tests':[]},{'plan_sha256':'0'*64}):
        with pytest.raises((ValidationError,ValueError)):
            api().ValidationPlan.model_validate(p.model_dump()|updates)
    from harness_core.configuration import ConfigError
    with pytest.raises((ConfigError,ValidationError)):
        request(p,command=['python','--password=super-secret'])


@pytest.mark.parametrize('status',['failed','blocked','not_run'])
def test_required_evidence_never_passes_unexecuted(status):
    p=plan(); r=request(p)
    e=api().make_evidence(r,status,reason='runtime_absent')
    result=api().validation_gate(p,[e])
    assert result['status']=='blocked'
    assert not result['publication_allowed']


def test_gate_checks_full_request_identity_and_result_hash():
    p=plan(); records=[]
    for test in p.tests:
        r=request(p,test.test_id)
        records.append(api().make_evidence(r,'passed',scope=test.scope,result={'value':'0.30'},observed=True))
    assert api().validation_gate(p,records)['status']=='passed'
    for field,value in [('candidate_sha256','0'*64),('client_id','beta'),('plan_revision',2),
        ('practice_pack_sha256','f'*64),('result_sha256','0'*64),('observed',False)]:
        bad=records[0].model_copy(update={field:value})
        assert api().validation_gate(p,[bad,records[1]])['status']=='blocked'


def test_missing_required_and_advisory_are_distinct():
    p=plan(impacts=['performance']); records=[]
    for t in p.tests:
        if t.required: records.append(api().make_evidence(request(p,t.test_id),'passed',scope=t.scope,result={},observed=True))
    result=api().validation_gate(p,records)
    assert result['status']=='passed' and result['advisory_missing']==['performance']
    assert api().validation_gate(p,[])['status']=='blocked'


def test_yaml_offline_and_python_parse_are_only_l0(scratch):
    from harness_local.validation import static_check
    p=plan('yaml-dabs'); r=request(p)
    e=static_check(p,r,b'bundle:\n  name: synthetic\n',filename='databricks.yml')
    assert e.status=='passed' and e.scope=='offline-syntax'
    assert api().validation_gate(plan('yaml-dabs',impacts=['integration']),[e])['status']=='blocked'
    p=plan(); r=request(p)
    assert static_check(p,r,b'def invalid(:\n',filename='x.py').status=='failed'


def test_static_controls_driver_cicd_and_relative_resources(scratch):
    from harness_local.validation import static_check
    p=plan('pyspark'); r=request(p)
    assert static_check(p,r,b'rows = df.collect()\n',filename='x.py').status=='failed'
    p=plan('cicd'); r=request(p)
    raw=b'jobs:\n  deploy:\n    needs: test\n    if: always()\n'
    assert static_check(p,r,raw,filename='ci.yml').status=='failed'
    p=plan('yaml-dabs'); r=request(p)
    raw=b'resources:\n  jobs:\n    job:\n      tasks:\n      - spark_python_task:\n          python_file: ../src/job.py\n'
    root=scratch; (root/'resources').mkdir(); (root/'src').mkdir()
    e=static_check(p,r,raw,filename='resources/job.yml',root=root)
    assert e.status=='failed'
    (root/'src/job.py').write_text('pass')
    assert static_check(p,r,raw,filename='resources/job.yml',root=root).status=='passed'


def test_rows_schema_nullability_decimal_and_tolerances():
    compare=api().compare_result
    expected={'schema':[{'name':'amount','type':'decimal(18,2)','nullable':True}],
        'rows':[['10.00'],['20.00'],[None]],'sum':'30.00'}
    assert compare(expected,expected|{'rows':list(reversed(expected['rows']))},unordered=True)
    assert not compare(expected,expected|{'sum':'30.01'})
    assert not compare(expected,expected|{'schema':[{'name':'amount','type':'decimal(18,2)','nullable':False}]})
    assert compare({'value':1.0},{'value':1.0001},absolute_tolerance=0.001)
    assert not compare({'value':1.0},{'value':1.1},absolute_tolerance=0.001)


def test_examples_match_schemas():
    import jsonschema
    root=Path(__file__).resolve().parents[1]
    for kind in ('validationplan','validationrequest','validationevidence','sandboxtarget','workerruntime'):
        schema=json.loads((root/'schemas'/f'{kind}.schema.json').read_text())
        value=json.loads((root/'docs/examples/validation'/f'{kind}.json').read_text())
        jsonschema.validate(value,schema)
