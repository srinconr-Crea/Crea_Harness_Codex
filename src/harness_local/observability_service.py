"""Read-only reports; state is serialized only to the selected output stream."""
import json

from pydantic import Field, ValidationError

from harness_core.configuration import ConfigError, pairs, safe_path
from harness_core.contracts import Contract, ID
from harness_core.observability import ActivityEvent, Timestamp, activity_report, desktop_usage


class UsageInput(Contract):
    client_id: ID
    hu_id: ID
    attempt: int = Field(ge=1)
    observed_at: Timestamp
    events: list[ActivityEvent] = Field(max_length=1000)


def load_input(path):
    # Separate loader: legacy load_document correctly rejects credential-bearing documents,
    # whereas these observation contracts redact payloads and allow numeric token fields.
    try:
        with safe_path(path).open('rb') as stream:
            raw = stream.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise ConfigError('document_too_large')
        value = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        if not isinstance(value, dict):
            raise ValueError()
        return value
    except (ValueError, UnicodeError, RecursionError):
        raise ConfigError('invalid_observation_document') from None


def parse(model, value):
    try:
        return model.model_validate(value)
    except (ValidationError, ValueError, TypeError, RecursionError):
        raise ConfigError('invalid_observation_document') from None


def usage_report(value):
    request = parse(UsageInput, value)
    identity = dict(client_id=request.client_id, hu_id=request.hu_id, attempt=request.attempt)
    activity = activity_report(request.events, **identity)
    usage = desktop_usage(**identity, observed_at=request.observed_at)
    return dict(schema_version=1, command='usage', status='partial', checks=[],
                activity=activity, usage=usage.model_dump(), certified=False)
