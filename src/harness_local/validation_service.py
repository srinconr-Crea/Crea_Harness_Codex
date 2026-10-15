"""Versioned CLI facade and evidence handoff to the existing HU gates."""
from typing import Literal
from pathlib import Path
import sqlite3

from pydantic import Field,ValidationError

from harness_core.configuration import ConfigError,read_bytes,safe_path
from harness_core.contracts import ID
from harness_core.guided import SafeContract,Text
from harness_core.quality import Technology
from harness_core.onboarding_plan import SHA,separate
from harness_core.validation import (ValidationPlan,ValidationRequest,ValidationEvidence,WorkerRuntime,SandboxTarget,
    validation_gate)


class SelectionInput(SafeContract):
    client_id: ID
    run_id: ID
    attempt: int = Field(ge=1)
    candidate_sha256: SHA
    plan_revision: int = Field(ge=1)
    technologies: list[Technology] = Field(min_length=1,max_length=8)
    impacts: list[Literal['logic','delta','runtime','integration','performance']] = Field(min_length=1,max_length=5)
    performance_baseline_sha256: SHA | None = None


class StaticInput(SafeContract):
    plan: ValidationPlan
    request: ValidationRequest
    source_path: Text
    root: Text | None = None


class WorkerInput(SafeContract):
    plan: ValidationPlan
    request: ValidationRequest
    runtime: WorkerRuntime | None
    source_path: Text
    function: ID
    cases: list[dict] = Field(max_length=100)
    expected: list = Field(max_length=100)
    unordered: bool = False
    absolute_tolerance: float = Field(default=0.0,ge=0)
    relative_tolerance: float = Field(default=0.0,ge=0)


class RemoteInput(SafeContract):
    plan: ValidationPlan
    request: ValidationRequest
    target: SandboxTarget | None
    state_dir: Text
    mode: Literal['sql','notebook','delta','job','bundle']
    expected: dict
    source_path: Text | None = None
    unordered: bool = False
    absolute_tolerance: float = Field(default=0.0,ge=0)
    relative_tolerance: float = Field(default=0.0,ge=0)


class GateInput(SafeContract):
    plan: ValidationPlan
    records: list[ValidationEvidence] = Field(max_length=64)


class AttachInput(GateInput):
    target_path: Text
    policy_path: Text
    binding_path: Text
    story_id: ID
    operation: ID
    actor: ID


def attach(service,story,operation,plan,records,*,actor):
    from harness_core.contracts import identifier
    identifier(operation); identifier(actor)
    run=service.run('status',story)['run']
    if (not run['plan'] or not run['candidate'] or run['state']!='validating' or
        (plan.client_id,plan.run_id,plan.attempt,plan.plan_revision,plan.candidate_sha256)!=
        (run['client_id'],run['run_id'],run['attempt'],run['plan']['revision'],run['candidate']['candidate_sha256']) or
        set(t.test_id for t in plan.tests if t.required)!=set(run['plan']['tests'])):
        return dict(schema_version=1,command='validate',status='blocked',checks=[dict(id='hu',status='blocked',code='validation_hu_mismatch')],publication_allowed=False)
    result=validation_gate(plan,records,allow_simulated=run['simulation'])
    if result['status']!='passed': return result
    from .quality_resources import load_quality
    from harness_core.onboarding_plan import canonical,sha
    if plan.practice_pack_sha256!=sha(canonical(load_quality().practices.model_dump())):
        return dict(result,status='blocked',checks=[dict(id='practices',status='blocked',code='stale_practices')])
    required={t.test_id for t in plan.tests if t.required}
    candidate_hashes={e['content_sha256'] for e in run['candidate']['entries'] if e['content_sha256']}
    for e in records:
        if e.test_id not in required or (e.simulated and run['simulation']): continue
        source_hash=e.result.get('source_sha256') if e.result else None
        if source_hash is None: source_hash=e.source_sha256
        if source_hash not in candidate_hashes:
            return dict(result,status='blocked',checks=[dict(id=e.test_id,status='blocked',code='candidate_source_mismatch')])
    for index,e in enumerate(records):
        if e.test_id not in required: continue
        data=dict(schema_version=1,id=e.test_id,candidate_sha256=e.candidate_sha256,status=e.status,
            simulated=e.simulated,actor=actor,kind='test',evidence_ref='validation-'+e.result_sha256[:24])
        response=service.run('evidence',story,operation[:48]+'-'+str(index),data)
        if response['status']=='blocked': return dict(result,status='blocked',checks=response['checks'])
    return result


def dispatch(action,raw):
    from .activity_execution import run
    raw=dict(raw)
    context=raw.pop('activity_context',None)
    if context is not None and action in ('static','worker','remote','bundle'):
        try:
            plan=ValidationPlan.model_validate(raw['plan'])
            request=ValidationRequest.model_validate(raw['request'])
        except (ValidationError,KeyError): raise ConfigError('invalid_validation_document') from None
        if any(getattr(plan,key)!=getattr(request,key) for key in ('client_id','run_id','attempt','plan_revision','candidate_sha256')) or request.plan_sha256!=plan.plan_sha256:
            raise ConfigError('activity_association_mismatch')
        from harness_core.onboarding_plan import canonical,sha
        return run(context,'validate_'+action,lambda:_dispatch(action,raw),expected_client=plan.client_id,validation_plan=plan,
            reconciler=action in ('remote','bundle'),reconcile_success=('passed','failed','blocked','not_run','unavailable'),
            request_sha256=sha(canonical(raw)))
    if context is not None: raise ConfigError('invalid_validation_document')
    return _dispatch(action,raw)


def _dispatch(action,raw):
    models=dict(plan=SelectionInput,static=StaticInput,worker=WorkerInput,remote=RemoteInput,bundle=RemoteInput,gate=GateInput,attach=AttachInput)
    try: data=models[action].model_validate(raw)
    except (ValidationError,ValueError,TypeError,KeyError): raise ConfigError('invalid_validation_document') from None
    try:
        if action=='plan':
            from .validation import select_plan
            plan=select_plan(**data.model_dump(exclude={'schema_version'}))
            return dict(schema_version=1,command='validate',status='ready',checks=[],plan=plan.model_dump()),0
        if action=='gate':
            result=validation_gate(data.plan,data.records)
            return result,1 if result['status']=='blocked' else 0
        if action=='attach':
            from .hu import HuService
            result=attach(HuService(data.target_path,data.policy_path,data.binding_path),data.story_id,
                data.operation,data.plan,data.records,actor=data.actor)
            return result,1 if result['status']=='blocked' else 0
        if action=='static':
            from .validation import static_check
            source=safe_path(data.source_path)
            filename=source.relative_to(safe_path(data.root)).as_posix() if data.root else source.name
            evidence=static_check(data.plan,data.request,read_bytes(source),filename=filename,root=data.root)
        elif action=='worker':
            from .validation_workers import run_worker
            evidence=run_worker(data.plan,data.request,data.runtime,source=read_bytes(data.source_path).decode('utf-8'),
                function=data.function,cases=data.cases,expected=data.expected,unordered=data.unordered,
                absolute_tolerance=data.absolute_tolerance,relative_tolerance=data.relative_tolerance)
        elif action=='bundle':
            from .validation_bundle import run_bundle
            if not data.source_path or data.mode!='bundle': raise ConfigError('invalid_validation_document')
            evidence=run_bundle(data.plan,data.request,data.target,read_bytes(data.source_path),state_dir=data.state_dir)
        else:
            from .validation_remote import RemoteValidator
            state=safe_path(data.state_dir)
            # State and input files remain external to client code; no global config mutation.
            evidence=RemoteValidator(state/'validation.sqlite3').run(data.plan,data.request,data.target,
                mode=data.mode,expected=data.expected,unordered=data.unordered,
                absolute_tolerance=data.absolute_tolerance,relative_tolerance=data.relative_tolerance,
                source=read_bytes(data.source_path).decode('utf-8') if data.source_path else None)
        result=dict(schema_version=1,command='validate',status=evidence.status,
            checks=[dict(id=evidence.test_id,status=evidence.status,code=evidence.reason or 'checked')],
            evidence=evidence.model_dump(),publication_allowed=False,certified=False)
        return result,0 if evidence.status=='passed' else 1
    except sqlite3.Error: raise ConfigError('validation_journal_unavailable') from None
    except (ValidationError,ValueError,TypeError): raise ConfigError('invalid_validation_document') from None
