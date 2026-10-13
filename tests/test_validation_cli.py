import json

from harness_local.cli import main
from test_validation import plan,request,api
from test_hu_lifecycle import hu


def run(scratch,capsys,action,value):
    path=scratch/'input.json'; path.write_text(json.dumps(value),encoding='utf-8')
    code=main(['validate',action,'--input',str(path),'--json'])
    return code,json.loads(capsys.readouterr().out)


def test_validation_cli_selection_static_and_missing_sandbox(scratch,capsys):
    value=dict(schema_version=1,client_id='alpha',run_id='run1',attempt=1,candidate_sha256='a'*64,
        plan_revision=1,technologies=['python'],impacts=['logic'])
    code,result=run(scratch,capsys,'plan',value)
    assert code==0 and result['command']=='validate'
    p=api().ValidationPlan.model_validate(result['plan']); r=request(p)
    source=scratch/'total.py'; source.write_text('def total(xs): return sum(xs)\n')
    code,result=run(scratch,capsys,'static',dict(schema_version=1,plan=p.model_dump(),request=r.model_dump(),source_path=str(source)))
    assert code==0 and result['evidence']['status']=='passed'
    p=plan('sql'); r=request(p,'sql-semantic')
    code,result=run(scratch,capsys,'remote',dict(schema_version=1,plan=p.model_dump(),request=r.model_dump(),
        target=None,state_dir=str(scratch/'state'),mode='sql',expected={}))
    assert code==1 and result['evidence']['reason']=='sandbox_not_selected'


def test_invalid_validation_cli_never_exposes_input(scratch,capsys):
    code,result=run(scratch,capsys,'plan',{'schema_version':99,'password':'not-for-output'})
    assert code==2 and result['status']=='invalid' and 'not-for-output' not in json.dumps(result)
    assert main(['validate','plan','--json'])==2
    assert json.loads(capsys.readouterr().out)['command']=='validate'


def test_gate_cli_required_not_run(scratch,capsys):
    p=plan()
    code,result=run(scratch,capsys,'gate',dict(schema_version=1,plan=p.model_dump(),records=[]))
    assert code==1 and result['status']=='blocked'


def test_validation_attach_uses_real_hu_gate_and_identity(hu,scratch):
    from harness_local.validation_service import attach
    from test_hu_lifecycle import plan as hu_plan,candidate
    s,client,_=hu
    hp=hu_plan(s,tests=['python-static','python-unit'])['run']['plan']
    s.run('approve','HU1','approve',dict(schema_version=1,actor='operator',confirmed=True,
        plan_sha256=hp['plan_sha256'],client_id='alpha',checkout_id='checkout',attempt=1,revision=1))
    s.run('transition','HU1','implement',dict(schema_version=1,state='implementing'))
    c=candidate(s,client); s.run('transition','HU1','validate',dict(schema_version=1,state='validating'))
    status=s.run('status','HU1')['run']
    p=plan(run_id=status['run_id'],candidate_sha256=c['candidate_sha256'])
    records=[api().make_evidence(request(p,t.test_id),'passed',scope=t.scope,result={},observed=True,simulated=True) for t in p.tests]
    unbound=[e.model_copy(update={'simulated':False}) for e in records]
    assert attach(s,'HU1','unbound',p,unbound,actor='tester')['status']=='blocked'
    assert not s.run('status','HU1')['run']['evidence']
    result=attach(s,'HU1','attach1',p,records,actor='tester')
    assert result['status']=='passed'
    assert s.run('transition','HU1','review',dict(schema_version=1,state='reviewing'))['status']=='ready'
    records[0]=records[0].model_copy(update={'candidate_sha256':'0'*64})
    assert attach(s,'HU1','attach2',p,records,actor='tester')['status']=='blocked'
