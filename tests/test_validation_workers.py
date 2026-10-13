"""Real credential-free worker protocol plus container boundary doubles."""
import json
import os
import subprocess
import sys

import pytest

from test_validation import plan,request,api


def test_worker_decimal_and_clean_session_protocol():
    from harness_local.validation_workers import WORKER
    payload={'source':'from decimal import Decimal\ndef total(xs): return str(sum((Decimal(x) for x in xs if x is not None), Decimal("0.00")))',
        'function':'total','cases':[{'args':[['0.10','0.20',None]]},{'args':[[]]}],
        'python_version':'.'.join(map(str,sys.version_info[:3])),'spark_version':None}
    # Only this harness-owned synthetic string is executed on host, never a client file.
    env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','PATH','TEMP','TMP')}
    result=subprocess.run([sys.executable,'-I','-c',WORKER],input=json.dumps(payload),text=True,
        capture_output=True,env=env,timeout=10)
    assert result.returncode==0 and json.loads(result.stdout)['values']==['0.30','0.00']
    payload['source']='def total(xs): return clean_df'
    result=subprocess.run([sys.executable,'-I','-c',WORKER],input=json.dumps(payload),text=True,capture_output=True,env=env,timeout=10)
    assert result.returncode==1 and json.loads(result.stdout)['status']=='failed'
    assert 'clean_df' not in result.stdout # no client exception/log leakage


def runtime(**changes):
    values=dict(schema_version=1,image='python@sha256:'+'e'*64,runtime='python-3.13',
        python_version='3.13.7',authorized=True)
    return api().WorkerRuntime(**(values|changes))


def test_container_has_no_host_mount_credentials_or_network():
    from harness_local.validation_workers import worker_command
    command=worker_command(runtime(),'harness-validation-123')
    assert '--network=none' in command and '--read-only' in command and '--cap-drop=ALL' in command
    assert '--security-opt=no-new-privileges' in command
    assert '--pull=never' in command and '--user=65534:65534' in command
    assert not any(c in command for c in ('-v','--mount','--env-file','--privileged'))


def test_missing_runtime_is_blocked_before_code_execution():
    from harness_local.validation_workers import run_worker
    p=plan(); r=request(p,'python-unit')
    e=run_worker(p,r,None,source='raise RuntimeError()',function='total',cases=[],expected=[])
    assert e.status=='blocked' and e.reason=='worker_runtime_absent'
    e=run_worker(p,r,runtime(authorized=False),source='raise RuntimeError()',function='total',cases=[],expected=[])
    assert e.status=='blocked' and e.reason=='worker_unauthorized'


def test_container_result_oracle_and_runtime_are_checked():
    from harness_local.validation_workers import run_worker,WORKER
    from harness_core.onboarding_plan import sha,canonical
    p=plan(); rt=runtime(); r=request(p,'python-unit',runtime_sha256='e'*64,tool_sha256=sha(WORKER.encode()),
        data_sha256=sha(canonical([{'args':[[]]}])),command=['docker','run',rt.image,'python','-I','worker'])
    def execute(argv,**kwargs):
        return subprocess.CompletedProcess(argv,0,json.dumps(dict(status='passed',runtime='3.13.7',spark_version=None,values=['0.30'])), '')
    e=run_worker(p,r,rt,source='def total(xs): pass',function='total',cases=[{'args':[[]]}],expected=['0.30'],execute=execute)
    assert e.status=='passed' and e.observed and e.simulated
    bad=run_worker(p,r,rt,source='def total(xs): pass',function='total',cases=[{'args':[[]]}],expected=['0.31'],execute=execute)
    assert bad.status=='failed'
    bad=run_worker(p,request(p,'python-unit'),rt,source='pass',function='x',cases=[],expected=[],execute=execute)
    assert bad.status=='blocked' and bad.reason=='worker_runtime_mismatch'


def test_timeout_cleans_only_owned_container():
    from harness_local.validation_workers import run_worker,WORKER
    from harness_core.onboarding_plan import sha,canonical
    p=plan(); rt=runtime(); r=request(p,'python-unit',runtime_sha256='e'*64,tool_sha256=sha(WORKER.encode()),
        data_sha256=sha(canonical([])),command=['docker','run',rt.image,'python','-I','worker']); calls=[]
    def execute(argv,**kwargs):
        calls.append(argv)
        if argv[1]=='run': raise subprocess.TimeoutExpired(argv,1)
        return subprocess.CompletedProcess(argv,0,'','')
    e=run_worker(p,r,runtime(),source='pass',function='x',cases=[],expected=[],execute=execute)
    assert e.status=='blocked' and e.reason=='worker_timeout'
    assert calls[-1][:3]==['docker','rm','--force']
    assert calls[-1][3].startswith('harness-validation-')


def test_worker_rejects_claimed_data_or_tool_hash():
    from harness_local.validation_workers import run_worker
    p=plan(); r=request(p,'python-unit',runtime_sha256='e'*64)
    e=run_worker(p,r,runtime(),source='pass',function='x',cases=[],expected=[])
    assert e.status=='blocked' and e.reason=='worker_request_mismatch'
