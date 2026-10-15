"""Opt-in PostToolUse adapter. No transcript or raw tool argument ingestion."""
from pathlib import Path

from pydantic import Field, ValidationError

from harness_core.contracts import ID
from harness_core.guided import SafeContract, Text
from harness_core.configuration import ConfigError, safe_path
from harness_core.onboarding_plan import canonical, sha
from .activity_ledger import now

DOCUMENTATION='https://learn.chatgpt.com/docs/hooks'
SUPPORTED_EVENTS=('PostToolUse',)


class HookAssociation(SafeContract):
    client_id: ID
    checkout_id: ID
    session_id: ID
    target_path: Text
    hu_id: ID
    attempt: int = Field(ge=1)
    confirmed: bool
    tool_operations: dict[str,ID] = Field(default_factory=dict,max_length=256)


def diagnose(*, events, trusted, script):
    available=bool(trusted and script and safe_path(script).is_file() and 'PostToolUse' in events)
    return dict(schema_version=1,status='partial' if available else 'unavailable',
        reason='documented_events_only' if available else 'native_actions_not_observed',
        supported_events=[e for e in SUPPORTED_EVENTS if e in events],script_present=bool(script and safe_path(script).is_file()),
        trusted=trusted,documentation_ref=DOCUMENTATION,tokens=None,cost_usd=None,
        usage_reason='supported_attributable_source_unavailable',hooks_observed=False)


def ingest(ledger, event, association, *, trusted, supported_events):
    if not trusted or event.get('hook_event_name') not in SUPPORTED_EVENTS or event.get('hook_event_name') not in supported_events:
        raise ConfigError('native_source_unavailable')
    try: association=HookAssociation.model_validate(association)
    except ValidationError: raise ConfigError('usage_unattributable') from None
    ledger.check_identity(association)
    if (not association.confirmed or association.session_id!=event.get('session_id') or
        safe_path(association.target_path)!=safe_path(ledger.binding.target_path) or
        safe_path(event.get('cwd',''))!=safe_path(association.target_path) or
        not isinstance(event.get('tool_use_id'),str) or not event['tool_use_id'] or
        not isinstance(event.get('tool_name'),str)):
        raise ConfigError('usage_unattributable')
    key=sha(canonical(dict(session=association.session_id,tool=event['tool_use_id'],event=event['hook_event_name'])))
    operation=association.tool_operations.get(event['tool_use_id'],key)
    with ledger.database() as db:
        existing=db.execute('SELECT payload FROM activity_events WHERE source=? AND idempotency_key=?',('hooks',key)).fetchone()
    import json
    at=json.loads(existing[0])['observed_at'] if existing else now()
    ledger.ingest([dict(schema_version=1,client_id=association.client_id,checkout_id=association.checkout_id,
        event_id=key,idempotency_key=key,operation_id=operation,scope='hu',hu_id=association.hu_id,attempt=association.attempt,
        kind='annotation',source='hooks',observed_at=at,status='not_run',payload={'tool_observed':True})])
    with ledger.database(write=True) as db:
        db.execute("UPDATE coverage SET status='documented_events_observed_partial' WHERE source='hooks'")


def main(argv=None):
    import argparse
    import json
    import sys
    from harness_core.configuration import load_document
    from .desktop_integration import selected
    from .activity_ledger import ActivityLedger
    parser=argparse.ArgumentParser()
    for name in ('path','policy','binding','association','definition','trusted-sha256'):
        parser.add_argument('--'+name,required=True)
    args=parser.parse_args(argv)
    try:
        definition=safe_path(args.definition)
        if sha(definition.read_bytes())!=args.trusted_sha256: raise ConfigError('native_source_unavailable')
        _,config=selected(args.path,args.policy,args.binding)
        data=sys.stdin.buffer.read(65537)
        if len(data)>65536: raise ConfigError('event_invalid')
        ingest(ActivityLedger(config['binding']),json.loads(data),load_document(args.association),
            trusted=True,supported_events=SUPPORTED_EVENTS)
        return 0
    except (ValueError,OSError,ConfigError):
        # Hook collection failure is not authority to block or repeat a client tool.
        print(json.dumps({'systemMessage':'Harness: native_actions_not_observed'}))
        return 0


if __name__=='__main__':
    raise SystemExit(main())
