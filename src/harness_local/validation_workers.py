"""Client code runs only in a selected pinned Linux container, never on host."""
import json
import os
import subprocess
import uuid

from harness_core.validation import validate_request,make_evidence,compare_result,WorkerRuntime
from harness_core.onboarding_plan import canonical,sha

# This runner is sent on stdin. No host bind mount, inherited env or credentials.
WORKER = r'''
import contextlib, io, json, os, sys
try:
    p=json.load(sys.stdin)
    version='.'.join(map(str,sys.version_info[:3]))
    if version!=p['python_version']: raise RuntimeError('runtime_mismatch')
    spark_version=None
    if p['spark_version']:
        import pyspark
        spark_version=pyspark.__version__
        if spark_version!=p['spark_version']: raise RuntimeError('runtime_mismatch')
    allowed={'PATH','TMPDIR','HOME','LANG','JAVA_HOME','SPARK_LOCAL_IP'}
    for key in list(os.environ):
        if key not in allowed: del os.environ[key]
    namespace={'__name__':'__candidate__'}
    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
        exec(compile(p['source'],'candidate.py','exec'),namespace)
        fn=namespace[p['function']]
        values=[fn(*c['args']) for c in p['cases']]
    print(json.dumps(dict(status='passed',runtime=version,spark_version=spark_version,values=values),allow_nan=False))
except BaseException:
    print(json.dumps(dict(status='failed')))
    sys.exit(1)
'''


def worker_command(runtime,name):
    return ['docker','run','--rm','--pull=never','--name',name,'--network=none','--read-only',
        '--cap-drop=ALL','--security-opt=no-new-privileges','--user=65534:65534','--pids-limit=128',
        '--cpus=1','--memory='+str(runtime.memory_mb)+'m','--memory-swap='+str(runtime.memory_mb)+'m',
        '--tmpfs=/tmp:rw,nosuid,nodev,size=256m,mode=1777','--workdir=/tmp','--env=HOME=/tmp',
        '--env=SPARK_LOCAL_IP=127.0.0.1','--log-driver=none','-i','--entrypoint=python',runtime.image,'-I','-c',WORKER]


def run_worker(plan,request,runtime,*,source,function,cases,expected,unordered=False,
    absolute_tolerance=0.0,relative_tolerance=0.0,execute=None):
    test=validate_request(plan,request)
    if test.layer!='L1': raise ValueError('worker_scope_mismatch')
    def blocked(reason): return make_evidence(request,'blocked',scope=test.scope,reason=reason)
    if request.source_sha256 is not None and sha(source.encode())!=request.source_sha256:
        return blocked('source_hash_mismatch')
    if runtime is None: return blocked('worker_runtime_absent')
    runtime=WorkerRuntime.model_validate(runtime.model_dump())
    if not runtime.authorized: return blocked('worker_unauthorized')
    if runtime.runtime!=request.runtime or runtime.image.split('@sha256:')[1]!=request.runtime_sha256:
        return blocked('worker_runtime_mismatch')
    if (request.tool_sha256!=sha(WORKER.encode()) or request.data_sha256!=sha(canonical(cases)) or
        request.command!=['docker','run',runtime.image,'python','-I','worker']):
        return blocked('worker_request_mismatch')
    if test.technology=='pyspark' and not runtime.spark_version: return blocked('spark_runtime_absent')
    payload=dict(source=source,function=function,cases=cases,python_version=runtime.python_version,spark_version=runtime.spark_version)
    if len(canonical(payload))>65536 or len(cases)>100 or not function.isidentifier(): return blocked('worker_input_limit')
    name='harness-validation-'+uuid.uuid4().hex
    command=worker_command(runtime,name)
    injected=execute is not None; execute=execute or subprocess.run
    env={k:v for k,v in os.environ.items() if k.upper() in ('PATH','SYSTEMROOT','WINDIR','TEMP','TMP')}
    try:
        result=execute(command,input=json.dumps(payload),text=True,capture_output=True,timeout=runtime.timeout_seconds,env=env)
        if len(result.stdout.encode('utf-8'))>65536: return blocked('worker_output_limit')
        value=json.loads(result.stdout)
        if value.get('runtime')!=runtime.python_version or value.get('spark_version')!=runtime.spark_version:
            if result.returncode: return make_evidence(request,'failed',scope=test.scope,reason='worker_failed',simulated=injected)
            return blocked('worker_runtime_mismatch')
        passed=result.returncode==0 and value.get('status')=='passed' and compare_result(expected,value.get('values'),
            unordered=unordered,absolute_tolerance=absolute_tolerance,relative_tolerance=relative_tolerance)
        # Persist observed command/runtime/source/data provenance, never stderr or client logs.
        observed=dict(values=value.get('values'),python_version=value['runtime'],spark_version=value['spark_version'],
            source_sha256=sha(source.encode()),data_sha256=sha(canonical(cases)),runner_sha256=sha(WORKER.encode()),
            command=['docker','run',runtime.image,'python','-I','worker'])
        return make_evidence(request,'passed' if passed else 'failed',scope=test.scope,
            reason=None if passed else 'worker_oracle_failed',result=observed,observed=True,simulated=injected)
    except FileNotFoundError: return blocked('worker_runtime_absent')
    except subprocess.TimeoutExpired:
        try: execute(['docker','rm','--force',name],capture_output=True,text=True,timeout=10,env=env)
        except (OSError,subprocess.SubprocessError): return blocked('worker_cleanup_required')
        return blocked('worker_timeout')
    except (OSError,ValueError,TypeError): return blocked('worker_unavailable')
