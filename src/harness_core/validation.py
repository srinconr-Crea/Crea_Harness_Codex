"""Independent strict validation v1 contracts and evidence checks."""
from datetime import datetime, timezone
from math import isclose, isfinite
from typing import Annotated, Any, Literal
from urllib.parse import urlsplit

from pydantic import Field, model_validator

from .contracts import ID
from .guided import SafeContract, Text
from .onboarding_plan import SHA, canonical, sha
from .quality import Technology

Status = Literal['passed','failed','blocked','not_run']
IDENTITY = ('plan_sha256','test_id','client_id','run_id','attempt','candidate_sha256',
    'plan_revision','practice_pack_sha256','data_sha256','runtime','runtime_sha256','tool_sha256','request_key','command','source_sha256')
TEST_SCOPES = {
    'python-unit':('python','L1','isolated-behavior'),
    'spark-unit':('pyspark','L1','isolated-spark'),
    'sql-semantic':('sql','L2','runtime-semantics'),
    'delta-semantic':('sql','L2','delta-runtime'),
    'runtime-semantic':('pyspark','L2','runtime-semantics'),
    'notebook-integration':('notebook','L3','fresh-job'),
    'job-integration':('notebook','L3','fresh-job'),
    'bundle-validate':('yaml-dabs','L3','authorized-bundle'),
    'performance':('general','L2','reproducible-baseline'),
}


class ValidationTest(SafeContract):
    test_id: ID
    technology: Technology
    layer: Literal['L0','L1','L2','L3']
    required: bool
    scope: Text
    rule_ids: list[ID] = Field(default_factory=list, max_length=64)

    @model_validator(mode='after')
    def scope_matches(self):
        expected=(self.technology,'L0','offline-syntax') if self.test_id==self.technology+'-static' else TEST_SCOPES.get(self.test_id)
        if expected!=(self.technology,self.layer,self.scope): raise ValueError('validation_test_scope_mismatch')
        if not self.required and self.test_id!='performance': raise ValueError('validation_required_downgrade')
        return self


class ValidationPlan(SafeContract):
    client_id: ID
    run_id: ID
    attempt: int = Field(ge=1)
    candidate_sha256: SHA
    plan_revision: int = Field(ge=1)
    practice_pack_sha256: SHA
    technologies: list[Technology] = Field(min_length=1,max_length=8)
    impacts: list[Literal['logic','delta','runtime','integration','performance']] = Field(min_length=1,max_length=5)
    tests: list[ValidationTest] = Field(min_length=1,max_length=64)
    catalog_test_ids: list[ID] = Field(max_length=64)
    performance_baseline_sha256: SHA | None = None
    plan_sha256: SHA

    @model_validator(mode='after')
    def integrity(self):
        if sha(canonical(self.model_dump(exclude={'plan_sha256'})))!=self.plan_sha256:
            raise ValueError('validation_plan_integrity')
        for items in (self.technologies,self.impacts,[t.test_id for t in self.tests],self.catalog_test_ids):
            if len(set(items))!=len(items): raise ValueError('duplicate_validation_selection')
        return self


class ValidationRequest(SafeContract):
    plan_sha256: SHA
    test_id: ID
    client_id: ID
    run_id: ID
    attempt: int = Field(ge=1)
    candidate_sha256: SHA
    plan_revision: int = Field(ge=1)
    practice_pack_sha256: SHA
    data_sha256: SHA
    runtime: Text
    runtime_sha256: SHA
    tool_sha256: SHA
    request_key: ID
    command: list[Text] = Field(min_length=1,max_length=32)
    source_sha256: SHA | None = None


class ValidationEvidence(ValidationRequest):
    status: Status
    scope: Text
    reason: ID | None = None
    observed: bool = False
    simulated: bool = False
    remote_run_id: int | None = Field(default=None,ge=1)
    result_uri: Text | None = None
    result_sha256: SHA | None = None
    result: dict[str,Any] | None = None
    started_at: Text
    finished_at: Text

    @model_validator(mode='after')
    def result_integrity(self):
        if self.result is not None:
            if len(canonical(self.result))>65536 or sha(canonical(self.result))!=self.result_sha256:
                raise ValueError('validation_result_integrity')
        if self.status=='passed' and (self.result is None or not self.observed):
            raise ValueError('unobserved_pass')
        start,end=(datetime.fromisoformat(t) for t in (self.started_at,self.finished_at))
        if start.tzinfo is None or end.tzinfo is None or end<start: raise ValueError('validation_timestamps')
        return self


class WorkerRuntime(SafeContract):
    image: Annotated[str,Field(pattern=r'^[a-zA-Z0-9./:_-]+@sha256:[0-9a-f]{64}$')]
    runtime: Text
    python_version: Annotated[str,Field(pattern=r'^3\.\d+\.\d+$')]
    spark_version: Annotated[str,Field(pattern=r'^\d+\.\d+\.\d+$')] | None = None
    authorized: bool
    timeout_seconds: int = Field(default=30,ge=1,le=300)
    memory_mb: int = Field(default=512,ge=128,le=8192)


class SandboxTarget(SafeContract):
    profile: ID
    host: Text
    caller_identity: Text
    execution_identity: Text
    job_id: int = Field(ge=1)
    task_key: ID
    runtime: Text
    volume: Text
    resources: list[Text] = Field(min_length=1,max_length=32)
    modes: list[Literal['sql','notebook','delta','job','bundle']] = Field(min_length=1,max_length=5)
    job_settings_sha256: SHA
    notebook_sha256: SHA
    authorized: bool
    synthetic: bool
    max_polls: int = Field(default=5,ge=1,le=60)
    poll_seconds: int = Field(default=1,ge=0,le=30)

    @model_validator(mode='after')
    def boundaries(self):
        url=urlsplit(self.host)
        if url.scheme!='https' or not url.hostname or url.username or url.password or url.query or url.fragment or url.path not in ('','/'):
            raise ValueError('invalid_validation_host')
        if not self.volume.startswith('/Volumes/') or len(self.volume.rstrip('/').split('/'))!=5:
            raise ValueError('invalid_validation_volume')
        for path in [self.volume,*self.resources]:
            if any(p in ('.','..') for p in path.split('/')) or '\\' in path: raise ValueError('invalid_validation_resource')
        if len(set(self.resources))!=len(self.resources): raise ValueError('duplicate_validation_resource')
        return self


def validate_request(plan,request):
    ValidationPlan.model_validate(plan.model_dump())
    ValidationRequest.model_validate(request.model_dump())
    for key in ('client_id','run_id','attempt','candidate_sha256','plan_revision','practice_pack_sha256','plan_sha256'):
        if getattr(plan,key)!=getattr(request,key): raise ValueError('validation_identity_mismatch')
    selected=next((t for t in plan.tests if t.test_id==request.test_id),None)
    if selected is None: raise ValueError('validation_test_not_selected')
    return selected


def make_evidence(request,status,*,scope='validation',reason=None,result=None,observed=False,
    simulated=False,remote_run_id=None,result_uri=None,started_at=None):
    now=datetime.now(timezone.utc).isoformat()
    return ValidationEvidence(**request.model_dump(),status=status,scope=scope,reason=reason,
        result=result,result_sha256=sha(canonical(result)) if result is not None else None,
        observed=observed,simulated=simulated,remote_run_id=remote_run_id,result_uri=result_uri,
        started_at=started_at or now,finished_at=now)


def validation_gate(plan,records,*,allow_simulated=False):
    checks=[]; advisory=[]
    for test in plan.tests:
        matches=[e for e in records if e.test_id==test.test_id]
        reason='missing'
        if len(matches)==1:
            e=matches[0]
            try:
                e=ValidationEvidence.model_validate(e.model_dump())
                validate_request(plan,ValidationRequest.model_validate({k:getattr(e,k) for k in IDENTITY}|{'schema_version':1}))
                reason=None if e.status=='passed' and e.observed and e.scope==test.scope and (not e.simulated or allow_simulated) else e.status if e.status!='passed' else 'scope_or_simulation'
                if test.test_id=='performance' and reason is None:
                    result=e.result or {}
                    profile=result.get('profile_sha256')
                    if (result.get('baseline_sha256')!=plan.performance_baseline_sha256 or not profile or
                        len(profile)!=64 or any(c not in '0123456789abcdef' for c in profile) or not result.get('metrics')):
                        reason='performance_baseline_required'
            except (ValueError,TypeError): reason='stale_or_invalid'
        elif len(matches)>1: reason='duplicate'
        if test.required: checks.append(dict(id=test.test_id,status='blocked' if reason else 'passed',code=reason or 'checked'))
        elif reason: advisory.append(test.test_id)
    return dict(schema_version=1,command='validate',status='blocked' if any(c['status']=='blocked' for c in checks) else 'passed',
        checks=checks,advisory_missing=advisory,publication_allowed=False,candidate_sha256=plan.candidate_sha256)


def compare_result(expected,actual,*,unordered=False,absolute_tolerance=0.0,relative_tolerance=0.0):
    """Decimals encoded as strings remain exact; tolerance applies only to floats."""
    if not (isfinite(absolute_tolerance) and isfinite(relative_tolerance)) or min(absolute_tolerance,relative_tolerance)<0:
        raise ValueError('invalid_tolerance')
    if type(expected)!=type(actual): return False
    if isinstance(expected,dict):
        return expected.keys()==actual.keys() and all(compare_result(v,actual[k],unordered=unordered if k=='rows' else False,
            absolute_tolerance=absolute_tolerance,relative_tolerance=relative_tolerance) for k,v in expected.items())
    if isinstance(expected,list):
        if unordered:
            return sorted(canonical(x) for x in expected)==sorted(canonical(x) for x in actual)
        return len(expected)==len(actual) and all(compare_result(a,b,absolute_tolerance=absolute_tolerance,
            relative_tolerance=relative_tolerance) for a,b in zip(expected,actual))
    if isinstance(expected,float):
        return isfinite(expected) and isfinite(actual) and isclose(expected,actual,abs_tol=absolute_tolerance,rel_tol=relative_tolerance)
    return expected==actual
