"""Typed conversational facade over HU; Codex remains the native coordinator."""
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError

from harness_core.configuration import ConfigError, safe_path
from harness_core.guided import SafeContract, Text
from harness_core.contracts import ID
from harness_core.hu import PlanInput, PlanRevision, approval_current, HuRun
from harness_core.onboarding_plan import canonical, sha
from .hu import HuService, scope_write
from .diagnostics import git_read


class WorkRequest(PlanInput):
    story_id: ID
    story: Text
    onboarding_plan: Text | None = None
    writer_actor: ID
    mode: Literal['native','supervised_single_agent']
    available_models: dict[str,list[str]]
    delegation_available: bool = False
    isolation_observed: bool = False
    native_task_refs: list[ID] = Field(default_factory=list,max_length=4)
    requires_independence: bool = False


class WorkService:
    def __init__(self, target, policy, binding):
        self.hu=HuService(target,policy,binding)

    def existing(self, story):
        try: return self.hu.run('status',story)['run']
        except ConfigError as error:
            if error.code!='hu_not_found': raise
            return None

    def onboarding(self, request):
        if request.onboarding_plan: return request.onboarding_plan
        if not self.hu.access: raise ConfigError('hu_preparation_required')
        path=self.hu.state/('setup-'+self.hu.access.run_id)/'journal.json'
        from .environment_setup import SetupJournal
        from harness_core.onboarding_plan import load_json
        journal=load_json(path,SetupJournal)
        if journal.state!='completed': raise ConfigError('hu_preparation_required')
        return journal.child_path

    def preview(self, raw):
        required=('story_id','story','writer_actor','criteria','paths','operations','tests','mode','available_models')
        questions=[key for key in required if not raw.get(key) and key!='available_models']
        if 'available_models' not in raw: questions.append('available_models')
        if questions: return dict(schema_version=1,command='work',status='blocked',checks=[],questions=questions,reason='missing_decision')
        try: request=WorkRequest.model_validate(raw)
        except ValidationError: raise ConfigError('invalid_work_document') from None
        if not self.hu.access: raise ConfigError('hu_preparation_required')
        prepared=self.hu.prepared(self.onboarding(request))
        for role in prepared.request.catalog.roles:
            if role.activated and (role.model not in request.available_models or role.effort not in request.available_models[role.model]):
                return self.blocked('model_unavailable')
        if request.mode=='native' and not request.delegation_available: return self.blocked('native_delegation_unavailable')
        if request.requires_independence and (request.mode!='native' or not request.isolation_observed):
            return self.blocked('native_isolation_unavailable')
        for path in request.paths:
            scope_write(self.hu.access,self.hu.config['policy'],path.rstrip('/')+('/scope-check' if path.endswith('/') else ''),request.paths)
        values=request.model_dump(include=set(PlanInput.model_fields))
        values['sources']={**values['sources'],'story':'user','binding':'local','base':'local'}
        base=git_read(self.hu.target,'rev-parse','HEAD')
        values['decisions']=[*values['decisions'],request.story,'coordination='+request.mode,'base='+base]
        if request.mode=='supervised_single_agent': values['max_delegations']=0
        existing=self.existing(request.story_id)
        if existing and existing['base']!=base: return self.blocked('base_changed')
        context=self.hu.context_hash()
        previous=(existing or {}).get('plan')
        same=previous and all(previous[k]==v for k,v in values.items()) and previous['context_sha256']==context
        number=previous['revision'] if same else previous['revision']+1 if previous else 1
        revision=dict(**values,revision=number,context_sha256=context)
        plan=PlanRevision.model_validate({**revision,'plan_sha256':sha(canonical(revision))})
        return dict(schema_version=1,command='work',status='ready',checks=[],questions=[],
            attempt=(existing or {}).get('attempt',1),
            plan=plan.model_dump(),request=request.model_dump(),onboarding_plan=self.onboarding(request),
            coordination=request.mode,native_task_refs=request.native_task_refs,native_evidence_state='submitted_unverified',
            independent_review_observed=False,certified=False,publication_allowed=False)

    def blocked(self, reason):
        return dict(schema_version=1,command='work',status='blocked',checks=[],questions=[],reason=reason,
            certified=False,publication_allowed=False)

    def start(self, raw, authorization):
        preview=self.preview(raw)
        if preview['status']!='ready': return preview
        plan=preview['plan']; request=WorkRequest.model_validate(preview['request'])
        if authorization!=plan['plan_sha256']: raise ConfigError('plan_stale')
        key=sha(canonical(dict(story=request.story_id,plan=authorization,attempt=preview['attempt'])))[:48]
        existing=self.existing(request.story_id)
        if existing:
            if existing['writer_actor']!=request.writer_actor or existing['onboarding_plan']!=preview['onboarding_plan']:
                raise ConfigError('hu_identity_mismatch')
            if existing['state'] in ('failed','cancelled','published'): raise ConfigError('work_attempt_required')
        else:
            self.hu.run('start',request.story_id,key+'s',dict(schema_version=1,onboarding_plan=preview['onboarding_plan'],
                writer_actor=request.writer_actor,simulation=False))
        planned=self.hu.run('plan',request.story_id,key+'p',{k:v for k,v in plan.items() if k in PlanInput.model_fields})
        if planned['status']=='blocked': return planned
        if (planned['run']['attempt']!=preview['attempt'] or not planned['run']['plan'] or
            planned['run']['plan']['plan_sha256']!=authorization): raise ConfigError('plan_stale')
        return self.hu.run('approve',request.story_id,key+'a',dict(schema_version=1,actor=request.writer_actor,confirmed=True,
            client_id=self.hu.config['binding'].client_id,checkout_id=self.hu.config['binding'].checkout_id,
            attempt=planned['run']['attempt'],revision=plan['revision'],plan_sha256=authorization))

    def status(self, story):
        result=self.hu.run('status',story)
        run=HuRun.model_validate(result['run'])
        from .activity_ledger import ActivityLedger
        ledger=ActivityLedger(self.hu.config['binding'])
        pending=ledger.report(dict(schema_version=1,hu_id=story))['incomplete_operations'] if ledger.path.exists() else None
        result.update(command='work',approval_current=approval_current(run),
            activity_pending_operations=pending,activity_coverage='ledger_missing' if pending is None else 'harness_commands',
            local_state=run.state,remote_state='not_checked',publication_state='blocked',
            next_action=('reconcile_pending' if pending else 'review_plan' if not approval_current(run) else 'reconcile_pending' if run.blocked_reason else
                'implement' if run.state=='approved' else 'validate_or_review'),
            independent_review_observed=any(e.kind=='review' and e.status=='passed' and not e.simulated for e in run.evidence))
        return result

    def resume(self, story, operation):
        result=self.hu.run('resume',story,operation,{'schema_version':1})
        if result['status']=='blocked': return result
        return self.status(story)
