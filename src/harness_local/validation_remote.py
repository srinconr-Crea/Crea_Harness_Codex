"""Explicit synthetic job adapters; durable reconciliation before any resubmit."""
import json
import base64
import os
from pathlib import Path
import sqlite3
import subprocess
import time

from harness_core.configuration import ConfigError, safe_path, pairs
from harness_core.onboarding_plan import canonical,sha
from harness_core.validation import (SandboxTarget,ValidationEvidence,IDENTITY,
    validate_request,make_evidence,compare_result)


class DatabricksCLI:
    """Only allowlisted existing single-task notebook jobs; no deploy/create/delete."""
    def __init__(self,execute=None):
        self.simulated=execute is not None
        self.execute=execute or subprocess.run

    def call(self,target,args):
        # Ignore ambient auth overrides; the user-selected profile supplies auth.
        env={k:v for k,v in os.environ.items() if not k.upper().startswith(('DATABRICKS_','ARM_','AZURE_','AWS_','GOOGLE_'))}
        result=self.execute(['databricks',*args,'--profile',target.profile,'--output','json'],
            capture_output=True,text=True,timeout=30,env=env)
        if result.returncode: raise ConfigError('remote_service_unavailable')
        if len(result.stdout.encode('utf-8'))>1024*1024: raise ConfigError('remote_output_limit')
        return json.loads(result.stdout,object_pairs_hook=pairs)

    def bundle_validate(self,target,stage):
        env={k:v for k,v in os.environ.items() if not k.upper().startswith(('DATABRICKS_','ARM_','AZURE_','AWS_','GOOGLE_'))}
        value=self.execute(['databricks','bundle','validate','--profile',target.profile,'--output','json'],
            cwd=stage,env=env,capture_output=True,text=True,timeout=30)
        if value.returncode or len(value.stdout.encode())>65536: raise ValueError('bundle_validate_failed')
        return json.loads(value.stdout,object_pairs_hook=pairs)

    def preflight(self,t):
        auth=self.call(t,['auth','describe'])
        # CLI auth describe may return host at top level or in details.
        host=auth.get('host') or auth.get('details',{}).get('host')
        caller=self.call(t,['current-user','me']).get('userName')
        job=self.call(t,['jobs','get',str(t.job_id)])
        settings=job['settings']; tasks=settings.get('tasks',[])
        if len(tasks)!=1 or tasks[0].get('task_key')!=t.task_key or tasks[0].get('existing_cluster_id'):
            raise ConfigError('sandbox_job_unsupported')
        task=tasks[0]
        if set(task)-{'task_key','description','timeout_seconds','max_retries','min_retry_interval_millis',
            'retry_on_timeout','notebook_task','new_cluster','job_cluster_key','libraries','run_if','email_notifications',
            'notification_settings','health','webhook_notifications','disable_auto_optimization'}:
            raise ConfigError('sandbox_job_unsupported')
        if not task.get('notebook_task') or task.get('libraries'):
            raise ConfigError('sandbox_job_unsupported')
        cluster=task.get('new_cluster')
        if not cluster:
            cluster=next((j['new_cluster'] for j in settings.get('job_clusters',[])
                if j['job_cluster_key']==task.get('job_cluster_key')),None)
        if not cluster: raise ConfigError('sandbox_runtime_unverified')
        # A certified template must not carry credentials, init scripts or external mounts.
        if any(cluster.get(k) for k in ('init_scripts','spark_env_vars','docker_image','instance_pool_id','aws_attributes','azure_attributes','gcp_attributes')):
            raise ConfigError('sandbox_cluster_unsupported')
        run_as=settings.get('run_as',job.get('run_as',{}))
        identity=run_as.get('service_principal_name') or run_as.get('user_name')
        parameters={v['name']:v.get('default','') for v in settings.get('parameters',[])}
        notebook=task['notebook_task']
        if notebook.get('source','WORKSPACE')!='WORKSPACE' or notebook.get('base_parameters'):
            raise ConfigError('sandbox_parameters_unverified')
        if parameters.get('harness_volume')!=t.volume or parameters.get('harness_synthetic')!='true':
            raise ConfigError('sandbox_parameters_unverified')
        exported=self.call(t,['workspace','export',notebook['notebook_path'],'--format','SOURCE'])
        notebook_hash=sha(base64.b64decode(exported['content'],validate=True))
        volume_parts=t.volume.strip('/').split('/')[1:]
        volume=self.call(t,['volumes','read','.'.join(volume_parts)])
        if volume.get('volume_type')!='MANAGED': raise ConfigError('sandbox_volume_unverified')
        return dict(profile=t.profile,host=host,caller_identity=caller,execution_identity=identity,
            job_id=job.get('job_id'),runtime=cluster.get('spark_version'),volume=t.volume,
            resources=[notebook['notebook_path']],job_settings_sha256=sha(canonical(settings)),notebook_sha256=notebook_hash,synthetic=True)

    def submit(self,t,r,key,mode,source=None):
        body={'idempotency_token':key,'job_parameters':{'harness_request':canonical(r.model_dump()).decode(),
            'harness_request_sha256':key,'harness_mode':mode,'harness_volume':t.volume,'harness_synthetic':'true'}}
        from .quality_resources import load_quality
        fixture=load_quality().fixture_bytes
        if not self.simulated and sha(fixture)!=r.data_sha256: raise ConfigError('remote_fixture_mismatch')
        body['job_parameters']['harness_fixture']=fixture.decode('utf-8')
        body['job_parameters']['harness_candidate']=source or ''
        result=self.call(t,['jobs','run-now',str(t.job_id),'--no-wait','--json',json.dumps(body)])
        return dict(remote_run_id=result['run_id'],request_sha256=key,job_id=t.job_id,
            client_id=r.client_id,run_id=r.run_id,attempt=r.attempt,candidate_sha256=r.candidate_sha256)

    def normalize(self,run):
        parameters=run.get('job_parameters',[])
        if isinstance(parameters,list): parameters={p['name']:p['value'] for p in parameters}
        request=json.loads(parameters.get('harness_request','{}'))
        state=run.get('state',{})
        return dict(remote_run_id=run['run_id'],job_id=run['job_id'],request_sha256=parameters.get('harness_request_sha256'),
            client_id=request.get('client_id'),run_id=request.get('run_id'),attempt=request.get('attempt'),
            candidate_sha256=request.get('candidate_sha256'),state=state.get('result_state') or state.get('life_cycle_state'))

    def find(self,t,key):
        result=self.call(t,['jobs','list-runs','--job-id',str(t.job_id),'--limit','25'])
        rows=result if isinstance(result,list) else result.get('runs',[])
        # A limited search can never establish absence; the validator won't resubmit.
        matches=[]
        for row in rows[:25]:
            full=self.call(t,['jobs','get-run',str(row['run_id'])])
            value=self.normalize(full)
            if value['request_sha256']==key: matches.append(value)
        return matches

    def poll(self,t,run_id):
        return self.normalize(self.call(t,['jobs','get-run',str(run_id)]))

    def output(self,t,run_id):
        full=self.call(t,['jobs','get-run',str(run_id)])
        tasks=full.get('tasks',[])
        if len(tasks)!=1 or tasks[0]['task_key']!=t.task_key: raise ConfigError('remote_task_mismatch')
        output=self.call(t,['jobs','get-run-output',str(tasks[0]['run_id'])])
        notebook=output.get('notebook_output',{})
        if notebook.get('truncated') or not notebook.get('result'): raise ConfigError('remote_result_absent')
        value=json.loads(notebook['result'],object_pairs_hook=pairs)
        # Root identity comes from the service metadata, not an echoed notebook field.
        value['remote_run_id']=full['run_id']; value['job_id']=full['job_id']
        return value


class RemoteValidator:
    def __init__(self,path,provider=None):
        self.path=Path(path)
        self.provider=provider or DatabricksCLI()

    def run(self,plan,request,target,*,mode,expected,unordered=False,absolute_tolerance=0.0,relative_tolerance=0.0,source=None):
        test=validate_request(plan,request)
        if test.layer not in ('L2','L3'): raise ValueError('remote_scope_mismatch')
        def blocked(reason,remote_run_id=None):
            return make_evidence(request,'blocked',scope=test.scope,reason=reason,remote_run_id=remote_run_id,
                simulated=self.provider.simulated)
        if target is None: return blocked('sandbox_not_selected')
        if (source is None)!=(request.source_sha256 is None) or (source is not None and (len(source.encode())>32768 or sha(source.encode())!=request.source_sha256)):
            return blocked('source_hash_mismatch')
        target=SandboxTarget.model_validate(target.model_dump())
        if not target.authorized or not target.synthetic: return blocked('sandbox_unauthorized')
        if mode not in target.modes or request.runtime!=target.runtime: return blocked('sandbox_identity_mismatch')
        if request.runtime_sha256!=sha(target.runtime.encode()) or request.tool_sha256!=target.notebook_sha256:
            return blocked('sandbox_hash_mismatch')
        if request.command!=['databricks','jobs','run-now',str(target.job_id),'--profile',target.profile]:
            return blocked('sandbox_command_mismatch')
        modes={'sql-semantic':'sql','delta-semantic':'delta','notebook-integration':'notebook','job-integration':'job','bundle-validate':'bundle'}
        if request.test_id in modes and modes[request.test_id]!=mode: return blocked('sandbox_mode_mismatch')
        try:
            observed=self.provider.preflight(target)
            fields=('profile','host','caller_identity','execution_identity','job_id','runtime','volume','resources','job_settings_sha256','notebook_sha256','synthetic')
            if any(observed.get(f)!=getattr(target,f) for f in fields): return blocked('sandbox_identity_mismatch')
        except (OSError,TimeoutError,subprocess.SubprocessError,ValueError,KeyError,ConfigError):
            return blocked('sandbox_preflight_unavailable')
        # Independent versioned journal; commit intent before sending network request.
        safe_path(self.path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        safe_path(self.path.parent)
        for suffix in ('','-journal','-wal','-shm'):
            path=safe_path(str(self.path)+suffix)
            if path.exists() and (not path.is_file() or path.stat().st_nlink!=1): raise ConfigError('validation_journal_conflict')
        key=sha(canonical(request.model_dump()))
        operation_hash=sha(canonical(dict(request=request.model_dump(),target=target.model_dump(),mode=mode,
            expected=expected,unordered=unordered,absolute_tolerance=absolute_tolerance,relative_tolerance=relative_tolerance)))
        scope=sha(canonical([request.client_id,request.run_id,request.attempt,request.test_id,request.request_key]))
        with sqlite3.connect(self.path,timeout=1) as db:
            db.execute('PRAGMA synchronous=FULL')
            version=db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0,1): raise ConfigError('validation_journal_version')
            if version==0:
                if db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchone():
                    raise ConfigError('validation_journal_version')
                db.execute('CREATE TABLE validation (scope TEXT PRIMARY KEY, operation TEXT NOT NULL, run INTEGER, evidence TEXT)')
                db.execute('PRAGMA user_version=1'); db.commit()
            columns=[row[1] for row in db.execute('PRAGMA table_info(validation)')]
            if columns!=['scope','operation','run','evidence']: raise ConfigError('validation_journal_version')
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT operation,run,evidence FROM validation WHERE scope=?',(scope,)).fetchone()
            if row and row[0]!=operation_hash: raise ConfigError('validation_operation_conflict')
            if row and row[2]: return ValidationEvidence.model_validate(json.loads(row[2]))
            first=row is None
            if first:
                db.execute('INSERT INTO validation VALUES (?,?,NULL,NULL)',(scope,operation_hash)); db.commit()
            else: db.commit()
            remote_id=row[1] if row else None
            try:
                if remote_id is None:
                    if first:
                        remote=self.provider.submit(target,request,key,mode,source=source) if source is not None else self.provider.submit(target,request,key,mode)
                    else:
                        matches=self.provider.find(target,key)
                        if len(matches)!=1: return blocked('remote_reconciliation_required')
                        remote=matches[0]
                    if not self.matches(remote,request,target,key): return blocked('remote_identity_mismatch')
                    remote_id=remote['remote_run_id']
                    db.execute('UPDATE validation SET run=? WHERE scope=?',(remote_id,scope)); db.commit()
                completed=False
                for index in range(target.max_polls):
                    remote=self.provider.poll(target,remote_id)
                    if not self.matches(remote,request,target,key) or remote['remote_run_id']!=remote_id:
                        return blocked('remote_identity_mismatch',remote_id)
                    if remote['state']=='SUCCESS': completed=True; break
                    if remote['state'] in ('FAILED','TIMEDOUT','CANCELED','SKIPPED','INTERNAL_ERROR'):
                        evidence=make_evidence(request,'failed',scope=test.scope,reason='remote_job_failed',remote_run_id=remote_id,
                            simulated=self.provider.simulated)
                        self.save(db,scope,evidence); return evidence
                    if index+1<target.max_polls and target.poll_seconds: time.sleep(target.poll_seconds)
                if not completed: return blocked('remote_poll_limit',remote_id)
                value=self.provider.output(target,remote_id)
                actual=value.get('result')
                valid=(value.get('request')=={k:getattr(request,k) for k in IDENTITY}
                    and value.get('job_id')==target.job_id and value.get('remote_run_id')==remote_id
                    and value.get('runtime')==target.runtime and value.get('execution_identity')==target.execution_identity
                    and value.get('data_sha256')==request.data_sha256 and value.get('source_sha256')==request.source_sha256
                    and value.get('result_sha256')==sha(canonical(actual)))
                passed=valid and compare_result(expected,actual,unordered=unordered,
                    absolute_tolerance=absolute_tolerance,relative_tolerance=relative_tolerance)
                evidence=make_evidence(request,'passed' if passed else 'failed',scope=test.scope,
                    reason=None if passed else 'remote_result_mismatch',result=actual if valid else None,observed=bool(valid),
                    simulated=self.provider.simulated,remote_run_id=remote_id,
                    result_uri=target.host+'/#job/'+str(target.job_id)+'/run/'+str(remote_id))
                self.save(db,scope,evidence); return evidence
            except (OSError,TimeoutError,subprocess.SubprocessError):
                return blocked('remote_reconciliation_required',remote_id)
            except (ValueError,TypeError,KeyError,ConfigError): return blocked('remote_result_invalid',remote_id)

    @staticmethod
    def matches(value,r,t,key):
        return all(value.get(k)==v for k,v in dict(request_sha256=key,job_id=t.job_id,
            client_id=r.client_id,run_id=r.run_id,attempt=r.attempt,candidate_sha256=r.candidate_sha256).items())

    @staticmethod
    def save(db,scope,evidence):
        db.execute('UPDATE validation SET evidence=? WHERE scope=?',(canonical(evidence.model_dump()).decode(),scope)); db.commit()
