"""Versioned, passive quality definitions. No tool or execution permissions."""
import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .configuration import ConfigError, pairs, safe_path, reject_secrets
from .contracts import Contract, ID, Relative

DOCUMENT_LIMIT = 1024 * 1024
Text = Annotated[str, Field(min_length=1, max_length=16384)]
Version = Annotated[str, Field(min_length=1, max_length=64)]
Technology = Literal['general', 'sql', 'python', 'notebook', 'pyspark', 'yaml-dabs', 'cicd', 'harness']


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


def unique(items, label):
    ids = [item.id for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate_' + label)


class Source(Strict):
    id: ID
    url: Text
    kind: Text
    scope: Text
    retrieved_on: Annotated[str, Field(pattern=r'^\d{4}-\d{2}-\d{2}$')]


class PracticeRule(Strict):
    id: ID
    technology: Technology
    severity: Literal['required', 'advisory']
    statement: Text
    applicability: Text
    evidence: Text
    source_refs: Annotated[list[ID], Field(min_length=1, max_length=256)]
    origin: Text
    execution_status: Literal['not_run'] = 'not_run'


class PracticePack(Contract):
    pack_id: ID
    version: Version
    status: Literal['draft', 'released']
    sources: Annotated[list[Source], Field(min_length=1, max_length=256)]
    rules: Annotated[list[PracticeRule], Field(min_length=1, max_length=256)]

    @model_validator(mode='after')
    def references(self):
        unique(self.sources, 'source'); unique(self.rules, 'rule')
        sources = {s.id for s in self.sources}
        if any(set(r.source_refs) - sources for r in self.rules):
            raise ValueError('missing_source')
        return self


class TestCase(Strict):
    id: ID
    technology: Technology
    operation: Text
    input: Text
    expected: Text
    source_rules: Annotated[list[ID], Field(min_length=1, max_length=256)]
    implementation_change: ID
    execution_mode: Text
    critical: bool
    status: Literal['not_run']


class TestCatalog(Contract):
    catalog_id: ID
    version: Version
    status: Literal['not_run']
    fixture_ref: Relative
    cases: Annotated[list[TestCase], Field(min_length=1, max_length=256)]

    @model_validator(mode='after')
    def case_ids(self):
        unique(self.cases, 'case')
        return self


class EvalCheck(Strict):
    id: ID
    description: Text
    critical: bool
    scorer: Text
    human_annotation_required: bool


class EvalExpected(Strict):
    known_defects: Annotated[list[ID], Field(max_length=256)]
    checks: Annotated[list[EvalCheck], Field(min_length=1, max_length=256)]


class EvalCase(Strict):
    id: ID
    role: ID
    task: Text
    input: dict
    expected: EvalExpected
    split: Literal['golden', 'holdout']
    source_rules: Annotated[list[ID], Field(min_length=1, max_length=256)]
    implementation_change: ID
    execution_mode: Text
    status: Literal['not_run']
    observed_output: None
    scores: None


class PromotionGate(Strict):
    critical_check_pass_rate: Literal[1]
    noncritical_check_pass_rate_min: Annotated[float, Field(ge=0.9, le=1)]
    blocked_or_not_run_is_pass: Literal[False]


class EvalCatalog(Contract):
    catalog_id: ID
    version: Version
    status: Literal['not_run']
    default_repetitions: Annotated[int, Field(ge=3, le=100)]
    promotion_gate: PromotionGate
    cases: Annotated[list[EvalCase], Field(min_length=1, max_length=256)]

    @model_validator(mode='after')
    def case_ids(self):
        unique(self.cases, 'case')
        unique([check for case in self.cases for check in case.expected.checks], 'check')
        return self


class Strengthening(Strict):
    rule_id: ID
    additional_evidence: Annotated[list[Text], Field(min_length=1, max_length=256)]


class TechnicalException(Strict):
    rule_id: ID
    reason: Text
    scope: Text
    reviewed_by: ID
    decision_ref: ID


class PracticeExtension(Contract):
    client_id: ID
    base_pack_id: ID
    base_version: Version
    sources: Annotated[list[Source], Field(max_length=256)] = Field(default_factory=list)
    rules: Annotated[list[PracticeRule], Field(max_length=256)] = Field(default_factory=list)
    strengthen: Annotated[list[Strengthening], Field(max_length=256)] = Field(default_factory=list)
    exceptions: Annotated[list[TechnicalException], Field(max_length=256)] = Field(default_factory=list)


class EffectivePractices(Strict):
    pack_id: ID
    version: Version
    client_id: ID | None
    rules: list[PracticeRule]
    sources: list[Source]
    additional_evidence: dict[str, list[str]]
    exceptions: list[TechnicalException]


def validate_catalogs(practices, tests, evals):
    for definition in (practices, tests, evals):
        if len(json.dumps(definition, ensure_ascii=False).encode('utf-8')) > DOCUMENT_LIMIT:
            raise ConfigError('document_too_large')
        reject_definition_secrets(definition)
    pack = PracticePack.model_validate(practices)
    tests = TestCatalog.model_validate(tests)
    evals = EvalCatalog.model_validate(evals)
    rules = {rule.id for rule in pack.rules}
    if any(set(case.source_rules) - rules for case in [*tests.cases, *evals.cases]):
        raise ConfigError('missing_rule')
    return pack, tests, evals


def decode_definition(raw, model):
    if len(raw) > DOCUMENT_LIMIT:
        raise ConfigError('document_too_large')
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs)
        reject_definition_secrets(value)
        return model.model_validate(value)
    except ConfigError:
        raise
    except (ValueError, TypeError, RecursionError):
        raise ConfigError('invalid_quality_definition') from None


def reject_definition_secrets(value):
    # Eval inputs may describe token telemetry, whose source is not a credential.
    # Only the explicit nullable metadata key is exempt; secret-like values still fail.
    def without_metadata(item):
        if isinstance(item, dict):
            return {k: without_metadata(v) for k, v in item.items()
                    if not (k == 'hu_token_source' and v is None)}
        if isinstance(item, list):
            return [without_metadata(v) for v in item]
        return item
    reject_secrets(without_metadata(value))


def load_definition(path, model):
    path = safe_path(path)
    try:
        with path.open('rb') as stream:
            return decode_definition(stream.read(DOCUMENT_LIMIT + 1), model)
    except OSError:
        raise ConfigError('quality_definition_unreadable') from None


def load_fixture(root, relative):
    from .contracts import relative as validate_relative
    validate_relative(relative)
    root = safe_path(root)
    path = safe_path(root / relative)
    if not path.is_relative_to(root):
        raise ConfigError('fixture_path_invalid')
    try:
        with path.open('rb') as stream:
            raw = stream.read(DOCUMENT_LIMIT + 1)
    except OSError:
        raise ConfigError('fixture_missing') from None
    if len(raw) > DOCUMENT_LIMIT:
        raise ConfigError('document_too_large')
    try:
        value = json.loads(raw, object_pairs_hook=pairs)
        reject_secrets(value)
        return value
    except (ValueError, TypeError, RecursionError):
        raise ConfigError('fixture_invalid') from None


def resolve_practices(pack, technology, extension=None, *, client_id=None, scope=None):
    if technology not in ('general', 'sql', 'python', 'notebook', 'pyspark', 'yaml-dabs', 'cicd'):
        raise ConfigError('unsupported_technology')
    # Copy inputs: effective plans cannot change the shared base or another client.
    pack = PracticePack.model_validate(pack.model_dump())
    extra = {}; exceptions = []
    if extension is not None:
        ext = PracticeExtension.model_validate(extension)
        if ext.client_id != client_id:
            raise ConfigError('client_mismatch')
        if (ext.base_pack_id, ext.base_version) != (pack.pack_id, pack.version):
            raise ConfigError('practice_base_mismatch')
        existing_rules = {r.id for r in pack.rules}
        existing_sources = {s.id for s in pack.sources}
        if any(r.id in existing_rules for r in ext.rules) or any(s.id in existing_sources for s in ext.sources):
            raise ConfigError('extension_conflict')
        pack = PracticePack.model_validate(dict(pack.model_dump(),
            rules=[r.model_dump() for r in [*pack.rules, *ext.rules]],
            sources=[s.model_dump() for s in [*pack.sources, *ext.sources]]))
        ids = {r.id for r in pack.rules}
        for item in ext.strengthen:
            if item.rule_id not in ids or item.rule_id in extra:
                raise ConfigError('extension_conflict')
            extra[item.rule_id] = list(item.additional_evidence)
        seen = set()
        for exception in ext.exceptions:
            key = (exception.rule_id, exception.scope)
            if exception.rule_id not in ids or key in seen:
                raise ConfigError('extension_conflict')
            seen.add(key)
            if exception.scope == scope:
                exceptions.append(exception)
    rules = [r for r in pack.rules if r.technology in ('general', technology)]
    ids = {r.id for r in rules}
    return EffectivePractices(pack_id=pack.pack_id, version=pack.version, client_id=client_id,
        rules=rules, sources=pack.sources,
        additional_evidence={k: v for k, v in extra.items() if k in ids},
        exceptions=[e for e in exceptions if e.rule_id in ids])


def definition_report(catalog, *, available_modes):
    missing = sorted({c.execution_mode for c in catalog.cases} - available_modes)
    return dict(schema_version=1, command='quality-definitions',
                status='blocked' if missing else 'not_run', execution_status='not_run',
                missing_modes=missing, observed_output=None, scores=None)


def compare_findings(case, observed_defects):
    """Independent exact-set rubric; not a runner or full eval certificate."""
    expected = set(case.expected.known_defects)
    observed = set(observed_defects)
    missing, false_positives = sorted(expected - observed), sorted(observed - expected)
    return dict(passed=not missing and not false_positives,
                missed_defects=missing, false_positives=false_positives)
