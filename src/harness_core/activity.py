"""Versioned ledger contracts, independent of the v1 observation import format."""
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .contracts import Contract, ID
from .observability import Timestamp, Duration, UsageObservation as ObservedUsage, public_text, redact
from .onboarding_plan import canonical


class ActivityEvent(Contract):
    client_id: ID
    checkout_id: ID
    event_id: ID
    operation_id: ID
    idempotency_key: ID
    source: Literal['harness_commands', 'imported', 'hooks']
    scope: Literal['setup', 'hu']
    hu_id: ID | None = None
    attempt: int | None = Field(default=None, ge=1)
    role: ID | None = None
    kind: Literal['start', 'result', 'retry', 'test', 'gate', 'annotation']
    observed_at: Timestamp
    duration_ms: Duration | None = None
    status: Literal['pending', 'passed', 'failed', 'blocked', 'not_run'] = 'pending'
    candidate_sha256: str | None = Field(default=None, pattern=r'^[0-9a-f]{64}$')
    request_sha256: str | None = Field(default=None, pattern=r'^[0-9a-f]{64}$')
    revision: int | None = Field(default=None, ge=1)
    action: ID | None = None
    reason: ID | None = None
    payload: dict = Field(default_factory=dict)
    redacted: bool = False

    @model_validator(mode='after')
    def validate_event(self):
        for name in ('client_id', 'checkout_id', 'event_id', 'operation_id', 'idempotency_key', 'hu_id', 'role'):
            if getattr(self, name) is not None: public_text(getattr(self, name))
        if self.scope == 'setup' and any(v is not None for v in (self.hu_id, self.attempt, self.role)):
            raise ValueError('setup_has_no_hu')
        if self.scope == 'hu' and not self.hu_id: raise ValueError('hu_association_required')
        if self.kind == 'start' and (self.status != 'pending' or self.duration_ms is not None):
            raise ValueError('invalid_start')
        if self.kind == 'result' and self.status == 'pending': raise ValueError('invalid_result')
        if len(canonical(self.payload)) > 16384: raise ValueError('payload_too_large')
        safe = redact(self.payload)
        self.redacted = self.redacted or safe != self.payload
        self.payload = safe
        return self


class UsageObservation(ObservedUsage):
    checkout_id: ID
    source_event_id: ID
    operation_id: ID | None = None
    # Scope intervals explicitly prevent aggregation of overlapping receipts.
    period_start: Timestamp
    period_end: Timestamp

    @model_validator(mode='after')
    def interval(self):
        from datetime import datetime
        if datetime.fromisoformat(self.period_start) > datetime.fromisoformat(self.period_end):
            raise ValueError('invalid_usage_period')
        public_text(self.checkout_id); public_text(self.source_event_id)
        return self


class LedgerQuery(Contract):
    client_id: ID | None = None
    checkout_id: ID | None = None
    hu_id: ID | None = None
    attempt: int | None = Field(default=None, ge=1)
    role: ID | None = None
    since: Timestamp | None = None
    until: Timestamp | None = None


class LedgerReport(Contract):
    client_id: ID
    checkout_id: ID
    counts: dict[str, int]
    events: list[ActivityEvent]
    usage: list[UsageObservation]
    incomplete_operations: int
    failed_operations: int
    duration_ms: Duration
    incomplete_durations: int = 0
    blocked_operations: int = 0
    retries: int = 0
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    unavailable_reason: str = 'supported_attributable_source_unavailable'
    measurement_conflicts: list[str] = Field(default_factory=list)
    coverage: dict[str, str]
