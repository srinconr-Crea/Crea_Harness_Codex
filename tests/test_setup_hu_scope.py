import json

from harness_core.onboarding_plan import canonical,sha
from harness_core.setup import SetupInput,SetupPlan
from test_setup_contracts import inputs
from test_hu_lifecycle import hu,approved,candidate,git,plan


def attach(service,client, *, initialize_activity=True, **scope_changes):
    raw=inputs(client)
    raw['access_scope'].update(read_allow=['src/','tests/'],write_allow=['src/'],deny=[])
    raw['access_scope'].update(scope_changes)
    value=dict(schema_version=1,kind='setup_plan',run_id='scope',inputs=SetupInput.model_validate(raw).model_dump(),
        input_hashes={},child_plans={},child_payloads={},setup_operations=[],stages=[],technical_reads=['.git/HEAD','.git/index','.git/config'],
        integration_writes=[p for p in git(client['target'],'ls-files','-z').decode().split('\0') if p],
        effects=[],applicable=True,blockers=[])
    setup=SetupPlan.model_validate({**value,'plan_sha256':sha(canonical(value))})
    client['binding'].with_name(client['binding'].name+'.setup.json').write_bytes(canonical(setup.model_dump()))
    if initialize_activity:
        from harness_local.activity_ledger import ActivityLedger
        ActivityLedger(service.config['binding']).initialize()


def test_setup_scope_blocks_hu_write_plan(hu):
    service,client,_=hu
    attach(service,client)
    result=plan(service)
    assert result['status']=='blocked' and result['run']['blocked_reason']=='access_denied'


def test_external_edit_outside_access_scope_blocks_gate_without_reading(hu):
    service,client,_=hu
    attach(service,client)
    plan(service,paths=['src/total.py'])
    p=service.run('status','HU1')['run']['plan']
    service.run('approve','HU1','a',dict(schema_version=1,actor='operator',confirmed=True,
        plan_sha256=p['plan_sha256'],client_id='alpha',checkout_id='checkout',attempt=1,revision=p['revision']))
    c=candidate(service,client)
    assert c['entries'][0]['path']=='src/total.py'
    (client['target']/'outside.py').write_bytes(b'forbidden')
    result=service.run('candidate','HU1','outside',{'schema_version':1})
    assert result['status']=='blocked' and result['run']['blocked_reason']=='access_denied'


def test_scope_drift_invalidates_old_approval(hu):
    service,client,_=hu
    approved(service)
    attach(service,client)
    result=service.run('status','HU1')
    assert result['status']=='blocked' and result['run']['approval'] is None
    assert result['run']['blocked_reason']=='context_changed'


def test_status_reloads_updated_policy_binding_and_scope_before_comparing(hu):
    service,client,_=hu
    approved(service)
    attach(service,client)
    policy=json.loads(client['policy'].read_bytes()); policy['max_bytes']+=1
    client['policy'].write_bytes(canonical(policy))
    binding=json.loads(client['binding'].read_bytes()); binding['policy_sha256']=sha(client['policy'].read_bytes())
    client['binding'].write_bytes(canonical(binding))
    attach(service,client,initialize_activity=False)
    result=service.run('status','HU1')
    assert result['status']=='blocked' and result['run']['approval'] is None
    assert service.config['binding'].policy_sha256==binding['policy_sha256']
