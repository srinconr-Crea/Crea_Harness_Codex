"""Service doubles exercise actual preflight, journal and reconciliation logic."""
import json
import subprocess

import pytest

from test_validation import plan,request,api
from harness_core.onboarding_plan import sha,canonical


def target(**updates):
    data=dict(schema_version=1,profile='sandbox',host='https://sandbox.example.invalid',
        caller_identity='caller@example.invalid',execution_identity='runner@example.invalid',job_id=7,
        task_key='validate',runtime='15.4.x-scala2.12',volume='/Volumes/sandbox/test/fixtures',
        resources=['/Workspace/sandbox/validate'],modes=['sql','notebook','delta','job','bundle'],
        job_settings_sha256='f'*64,notebook_sha256='e'*64,authorized=True,synthetic=True,max_polls=2,poll_seconds=0)
    return api().SandboxTarget(**(data|updates))


class ServiceDouble:
    simulated=True
    def __init__(self):
        self.calls=[]; self.runs={}; self.lost=False; self.busy=False; self.mismatch=None; self.target=target()
    def preflight(self,t):
        self.calls.append('preflight')
        return dict(profile=t.profile,host=t.host,caller_identity=t.caller_identity,execution_identity=t.execution_identity,
            job_id=t.job_id,runtime=t.runtime,volume=t.volume,resources=t.resources,
            job_settings_sha256=t.job_settings_sha256,notebook_sha256=t.notebook_sha256,synthetic=True)
    def find(self,t,key):
        self.calls.append('find')
        return [v for v in self.runs.values() if v['request_sha256']==key]
    def submit(self,t,r,key,mode):
        self.calls.append('submit')
        self.runs[11]=dict(remote_run_id=11,request_sha256=key,job_id=t.job_id,
            client_id=r.client_id,run_id=r.run_id,attempt=r.attempt,candidate_sha256=r.candidate_sha256)
        if self.lost: raise TimeoutError()
        return self.runs[11]
    def poll(self,t,run):
        self.calls.append('poll')
        return self.runs[run]|dict(state='RUNNING' if self.busy else 'SUCCESS')
    def output(self,t,run):
        self.calls.append('output')
        r=self.request
        value=dict(result={'rows':3,'sum':'30.00'},request={k:getattr(r,k) for k in api().IDENTITY},
            job_id=t.job_id,remote_run_id=run,runtime=t.runtime,execution_identity=t.execution_identity,
            data_sha256=r.data_sha256,result_sha256=sha(canonical({'rows':3,'sum':'30.00'})))
        if self.mismatch: value.update(self.mismatch)
        return value


def execute(scratch,s=None,t=None,r=None,**kwargs):
    from harness_local.validation_remote import RemoteValidator
    p=plan('sql',impacts=['delta']); t=t or target(); r=r or request(p,'delta-semantic',runtime=t.runtime,
        runtime_sha256=sha(t.runtime.encode()),tool_sha256=t.notebook_sha256,
        command=['databricks','jobs','run-now',str(t.job_id),'--profile',t.profile])
    s=s or ServiceDouble(); s.request=r
    return RemoteValidator(scratch/'validation.sqlite',s).run(p,r,t,mode='delta',expected={'rows':3,'sum':'30.00'},**kwargs)


def test_remote_selected_sandbox_and_result(scratch):
    e=execute(scratch)
    assert e.status=='passed' and e.observed and e.simulated and e.remote_run_id==11


@pytest.mark.parametrize('field,value',[('host','https://other.example.invalid'),('profile','other'),
    ('caller_identity','other'),('execution_identity','other'),('runtime','other'),('job_id',8),
    ('volume','/Volumes/other/test/fixtures'),('resources',['/Workspace/prod']),('job_settings_sha256','0'*64)])
def test_wrong_preflight_has_zero_remote_writes(scratch,field,value):
    s=ServiceDouble(); original=s.preflight
    s.preflight=lambda t: original(t)|{field:value}
    e=execute(scratch,s)
    assert e.status=='blocked' and e.reason=='sandbox_identity_mismatch'
    assert 'submit' not in s.calls


def test_missing_authorization_or_target_blocks_without_remote_call(scratch):
    s=ServiceDouble()
    assert execute(scratch,s,t=target(authorized=False)).status=='blocked'
    assert s.calls==[]
    from harness_local.validation_remote import RemoteValidator
    p=plan('sql'); r=request(p,'sql-semantic')
    e=RemoteValidator(scratch/'other.sqlite',s).run(p,r,None,mode='sql',expected={})
    assert e.reason=='sandbox_not_selected' and s.calls==[]


def test_lost_submit_reconciles_across_process_restart(scratch):
    s=ServiceDouble(); s.lost=True
    e=execute(scratch,s)
    assert e.status=='blocked' and e.reason=='remote_reconciliation_required'
    s.lost=False
    assert execute(scratch,s).status=='passed'
    assert s.calls.count('submit')==1 and 'find' in s.calls
    assert execute(scratch,s).status=='passed' and s.calls.count('submit')==1


def test_polling_limit_then_resume_without_resubmit(scratch):
    s=ServiceDouble(); s.busy=True
    e=execute(scratch,s)
    assert e.reason=='remote_poll_limit' and s.calls.count('poll')==2
    s.busy=False
    assert execute(scratch,s).status=='passed' and s.calls.count('submit')==1


@pytest.mark.parametrize('bad',[
    {'result_sha256':'0'*64},{'job_id':8},{'remote_run_id':12},{'runtime':'different'},
    {'execution_identity':'other'},{'data_sha256':'0'*64},{'request':{'client_id':'beta'}}])
def test_cross_identity_or_hash_never_receives_success(scratch,bad):
    s=ServiceDouble(); s.mismatch=bad
    assert execute(scratch,s).status=='failed'


def test_same_key_cannot_be_reused_for_changed_request_or_oracle(scratch):
    from harness_core.configuration import ConfigError
    execute(scratch)
    p=plan('sql',impacts=['delta']); t=target()
    r=request(p,'delta-semantic',runtime=t.runtime,data_sha256='0'*64,
        runtime_sha256=sha(t.runtime.encode()),tool_sha256=t.notebook_sha256,
        command=['databricks','jobs','run-now',str(t.job_id),'--profile',t.profile])
    with pytest.raises(ConfigError,match='validation_operation_conflict'):
        execute(scratch,r=r)
    from harness_local.validation_remote import RemoteValidator
    r=request(p,'delta-semantic',runtime=t.runtime,runtime_sha256=sha(t.runtime.encode()),tool_sha256=t.notebook_sha256,
        command=['databricks','jobs','run-now',str(t.job_id),'--profile',t.profile])
    with pytest.raises(ConfigError):
        RemoteValidator(scratch/'validation.sqlite',ServiceDouble()).run(p,r,t,mode='delta',expected={'rows':4})


def test_ambiguous_lookup_never_resubmits(scratch):
    s=ServiceDouble(); s.lost=True
    execute(scratch,s)
    s.find=lambda t,key: []
    assert execute(scratch,s).reason=='remote_reconciliation_required'
    assert s.calls.count('submit')==1


def test_cli_provider_uses_explicit_profile_and_idempotency():
    from harness_local.validation_remote import DatabricksCLI
    t=target(); p=plan('sql'); r=request(p,'sql-semantic',runtime=t.runtime); commands=[]
    def run(argv,**kw):
        commands.append(argv)
        return subprocess.CompletedProcess(argv,0,'{"run_id":11}','')
    provider=DatabricksCLI(execute=run)
    result=provider.submit(t,r,'a'*64,'sql')
    assert result['remote_run_id']==11
    argv=commands[-1]
    assert argv[:4]==['databricks','jobs','run-now','7'] and '--no-wait' in argv
    assert argv[argv.index('--profile')+1]=='sandbox'
    body=json.loads(argv[argv.index('--json')+1])
    assert body['idempotency_token']=='a'*64
    assert body['job_parameters']['harness_mode']=='sql'
    assert body['job_parameters']['harness_request']==canonical(r.model_dump()).decode()
