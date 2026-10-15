"""Explicit attribution for executors that also support global operations."""
from pydantic import Field,ValidationError

from harness_core.contracts import ID
from harness_core.guided import SafeContract, Text
from harness_core.configuration import ConfigError
from harness_core.onboarding_plan import canonical, sha
from .activity_ledger import ActivityLedger


class ActivityContext(SafeContract):
    target_path: Text
    policy_path: Text
    binding_path: Text
    hu_id: ID | None = None
    attempt: int | None = Field(default=None,ge=1)
    role: ID | None = None
    operation_id: ID


def operation_key(context, action):
    context=ActivityContext.model_validate(context)
    return sha(canonical(dict(action=action,operation=context.operation_id,hu=context.hu_id,attempt=context.attempt)))


def run(context, action, function, *, expected_identity=None, expected_binding=None, expected_client=None, validation_plan=None, reconciler=False, reconcile_success=('published',),request_sha256=None):
    if context is None: return function()
    from .desktop_integration import selected
    from .hu import HuService
    try: context=ActivityContext.model_validate(context)
    except ValidationError: raise ConfigError('invalid_activity_context') from None
    _,config=selected(context.target_path,context.policy_path,context.binding_path)
    binding=config['binding']
    if expected_client is not None and binding.client_id!=expected_client: raise ConfigError('ledger_identity_mismatch')
    if expected_binding is not None and binding!=expected_binding: raise ConfigError('ledger_identity_mismatch')
    if expected_identity is not None and expected_identity!=(binding.client_id,binding.checkout_id):
        raise ConfigError('ledger_identity_mismatch')
    if context.hu_id:
        status=HuService(context.target_path,context.policy_path,context.binding_path).run('status',context.hu_id)
        if context.attempt!=status['run']['attempt']: raise ConfigError('activity_association_mismatch')
        if validation_plan:
            state=status['run']
            if (not state['plan'] or not state['candidate'] or
                (validation_plan.client_id,validation_plan.run_id,validation_plan.attempt,validation_plan.plan_revision,validation_plan.candidate_sha256)!=
                (state['client_id'],state['run_id'],state['attempt'],state['plan']['revision'],state['candidate']['candidate_sha256'])):
                raise ConfigError('activity_association_mismatch')
    ledger=ActivityLedger(config['binding'])
    key=operation_key(context,action)
    original_key=key
    if reconciler:
        with ledger.database() as db:
            existing=db.execute('SELECT result_event,start_event FROM operations WHERE operation_id=?',(key,)).fetchone()
        if existing:
            import json
            if json.loads(existing[1]).get('request_sha256')!=request_sha256: raise ConfigError('ledger_operation_conflict')
            if existing[0]:
                if json.loads(existing[0])['status']=='passed': return function()
            import uuid
            key=sha((key+uuid.uuid4().hex).encode())
    with ledger.operation(key,scope='hu' if context.hu_id else 'setup',hu_id=context.hu_id,
        attempt=context.attempt,role=context.role,action=action,request_sha256=request_sha256) as outcome:
        result=function()
        value=result[0] if isinstance(result,tuple) else result
        status=value.get('status') if isinstance(value,dict) else None
        outcome['status']='blocked' if status in ('blocked','not_run','unavailable') else 'failed' if status in ('failed','invalid') else 'passed'
        outcome['pending']=status=='unknown'
        evidence=(value.get('evidence') or {}) if isinstance(value,dict) else {}
        outcome['candidate_sha256']=evidence.get('candidate_sha256')
        outcome['revision']=evidence.get('plan_revision')
        if reconciler and original_key!=key and status in reconcile_success: ledger.finish_pending(original_key,outcome['status'])
        return result
