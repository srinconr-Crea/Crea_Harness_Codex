"""Attributed observations. No private Desktop logs or account-quota attribution."""
import re
from collections import Counter
from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, Field, model_validator

from .configuration import ConfigError, reject_secrets
from .contracts import Contract, ID
from .onboarding_plan import canonical


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.tzinfo is None or 'T' not in value:
            raise ValueError()
    except ValueError:
        raise ValueError('timestamp_with_timezone_required') from None
    return value


def public_text(value):
    reject_secrets(value)
    if re.search(r'(?i)(bearer\s+|(?:password|secret|token|api[_-]?key)\s*[=:])', value):
        raise ValueError('sensitive_metadata')
    return value


Timestamp = Annotated[str, Field(max_length=64), AfterValidator(timestamp)]
Text = Annotated[str, Field(min_length=1, max_length=4096), AfterValidator(public_text)]
Duration = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Count = Annotated[int, Field(ge=0)]
State = Literal['passed', 'failed', 'blocked', 'not_run']
Surface = Literal['desktop', 'cli', 'harness-local']


def redact(value):
    """Drop unknown free text rather than claiming complete pattern-based secret detection.

    Only numeric/boolean/null payload measurements survive. Sources put public structured
    diagnostics in kind/status; private free text belongs in external, unexported evidence.
    """
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            try:
                reject_secrets(key)
            except ConfigError:
                continue
            if not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', key):
                continue
            if re.search(r'(?i)(password|secret|token|credential|key|authorization|cookie)', key):
                continue
            result[key] = redact(item)
        return result
    if isinstance(value, list):
        return [redact(item) for item in value]
    if type(value) in (bool, int) or value is None:
        return value
    if type(value) is float:
        import math
        return value if math.isfinite(value) else None
    return '[REDACTED]'


class ActivityEvent(Contract):
    client_id: ID
    hu_id: ID
    attempt: int = Field(ge=1)
    role: ID
    event_id: ID
    kind: Literal['duration', 'delegation', 'retry', 'test', 'remote', 'gate', 'annotation']
    source: Literal['harness-local', 'desktop-manual']
    observed_at: Timestamp
    duration_ms: Duration | None = None
    status: State
    payload: dict = Field(default_factory=dict)
    redacted: bool = False

    @model_validator(mode='after')
    def sanitize(self):
        for name in ('client_id', 'hu_id', 'role', 'event_id'):
            public_text(getattr(self, name))
        if len(canonical(self.payload)) > 16384:
            raise ValueError('payload_too_large')
        safe = redact(self.payload)
        self.redacted = self.redacted or safe != self.payload
        self.payload = safe
        return self


class UsageObservation(Contract):
    client_id: ID
    hu_id: ID
    attempt: int = Field(ge=1)
    source: Literal['unavailable', 'supported-session-receipt']
    scope: Literal['hu', 'session', 'account']
    surface: Surface = 'desktop'
    observed_at: Timestamp
    native_session_id: ID | None = None
    documentation_ref: Text | None = None
    association_ref: ID | None = None
    input_tokens: Count | None = None
    output_tokens: Count | None = None
    cached_tokens: Count | None = None
    cost_usd: Annotated[float, Field(ge=0, allow_inf_nan=False)] | None = None
    token_unit: Literal['tokens'] = 'tokens'
    cost_unit: Literal['USD'] = 'USD'
    reason: ID | None

    @model_validator(mode='after')
    def provenance(self):
        for name in ('client_id', 'hu_id', 'native_session_id', 'association_ref', 'reason'):
            if getattr(self, name) is not None:
                public_text(getattr(self, name))
        metrics = (self.input_tokens, self.output_tokens, self.cached_tokens, self.cost_usd)
        if self.source == 'unavailable':
            if any(v is not None for v in metrics) or not self.reason:
                raise ValueError('unavailable_must_be_null_with_reason')
        else:
            # Receipt import is a declared external CLI observation, never Desktop billing.
            if (self.scope != 'session' or self.surface != 'cli' or
                not all((self.native_session_id, self.documentation_ref, self.association_ref))):
                raise ValueError('supported_session_association_required')
            if self.cost_usd is not None:
                raise ValueError('billing_adapter_unavailable')
            if any(v is None for v in metrics) and not self.reason:
                raise ValueError('missing_measurement_reason')
        return self


def desktop_usage(*, client_id, hu_id, attempt, observed_at):
    return UsageObservation(schema_version=1, client_id=client_id, hu_id=hu_id,
        attempt=attempt, observed_at=observed_at, source='unavailable', scope='hu',
        reason='supported_attributable_source_unavailable')


def activity_report(events, *, client_id, hu_id, attempt):
    unique = {}; duplicates = 0
    for raw in events:
        event = ActivityEvent.model_validate(raw.model_dump() if isinstance(raw, ActivityEvent) else raw)
        if (event.client_id, event.hu_id, event.attempt) != (client_id, hu_id, attempt):
            raise ConfigError('activity_identity_mismatch')
        # Keys are scoped by identity, not source: source changes cannot replay an event.
        key = (event.role, event.event_id)
        value = event.model_dump()
        if key in unique:
            if unique[key] != value:
                raise ConfigError('event_id_conflict')
            duplicates += 1
        else:
            unique[key] = value
    values = list(unique.values())
    return dict(events=values, counts=dict(Counter(e['kind'] for e in values)),
                duplicates=duplicates, duration_ms=sum(e['duration_ms'] or 0 for e in values),
                coverage='submitted_events_only', hooks_certified=False,
                sources=sorted({e['source'] for e in values}))
