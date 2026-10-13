"""Manual evidence scoring and conservative promotion; no embedded LLM engine."""
from collections import Counter
from statistics import mean, pvariance
from typing import Literal

from pydantic import Field, model_validator

from .configuration import ConfigError
from .contracts import Contract, ID
from .observability import Duration, State, Surface, Text, Timestamp, public_text
from .onboarding_plan import SHA, canonical, sha
from .quality import Strict, compare_findings


class EvalProfile(Contract):
    profile_id: ID
    model: Text
    effort: Literal['low', 'medium', 'high', 'xhigh', 'max', 'ultra']
    surface: Surface
    dataset_sha256: SHA
    kit_sha256: SHA
    config_sha256: SHA
    runtime: Text
    tools: dict[ID, Text] = Field(min_length=1, max_length=64)
    roles_sha256: SHA
    practices_sha256: SHA
    configuration_evidence_ref: ID | None = None

    @model_validator(mode='after')
    def public_identity(self):
        public_text(self.profile_id)
        if self.configuration_evidence_ref:
            public_text(self.configuration_evidence_ref)
        for key in self.tools:
            public_text(key)
        return self


class CheckAnnotation(Strict):
    check_id: ID
    status: State
    evidence_ref: ID
    annotator: ID
    annotation_kind: Literal['human', 'deterministic', 'llm']
    reason: Text

    @model_validator(mode='after')
    def public_ids(self):
        for name in ('check_id', 'evidence_ref', 'annotator'):
            public_text(getattr(self, name))
        return self


class EvalOutput(Strict):
    observed_defects: list[ID] = Field(max_length=256)
    checks: list[CheckAnnotation] = Field(max_length=256)

    @model_validator(mode='after')
    def distinct(self):
        if len(set(self.observed_defects)) != len(self.observed_defects):
            raise ValueError('duplicate_finding')
        ids = [a.check_id for a in self.checks]
        if len(ids) != len(set(ids)):
            raise ValueError('duplicate_annotation')
        for item in self.observed_defects:
            public_text(item)
        return self


class EvalRun(Contract):
    run_id: ID
    case_id: ID
    role: ID
    profile_sha256: SHA
    repetition: int = Field(ge=1, le=100)
    surface: Surface
    mode: Literal['manual', 'automatic']
    status: State
    observed_at: Timestamp
    duration_ms: Duration | None
    artifact_ref: ID | None
    artifact_sha256: SHA | None
    output: EvalOutput | None
    simulated: bool

    @model_validator(mode='after')
    def artifact(self):
        for name in ('run_id', 'case_id', 'role', 'artifact_ref'):
            if getattr(self, name) is not None:
                public_text(getattr(self, name))
        if self.output is not None:
            if not self.artifact_ref or self.artifact_sha256 != sha(canonical(self.output.model_dump())):
                raise ValueError('artifact_hash_mismatch')
            if any(a.evidence_ref != self.artifact_ref for a in self.output.checks):
                raise ValueError('annotation_artifact_mismatch')
        elif self.status in ('passed', 'failed'):
            raise ValueError('observed_output_required')
        return self


class EvalScore(Contract):
    run_id: ID
    check_id: ID
    critical: bool
    status: State
    reason: ID
    evidence_ref: ID | None
    scorer: Literal['artifact-review-v1'] = 'artifact-review-v1'


def select_cases(catalog, *, milestone, purpose):
    if type(milestone) is not int or not 1 <= milestone <= 8:
        raise ConfigError('invalid_milestone')
    if purpose not in ('development', 'promotion'):
        raise ConfigError('invalid_eval_purpose')
    available = []; future = []
    for case in catalog.cases:
        number = int(case.implementation_change.split('-', 1)[0])
        if number > milestone:
            future.append(case)
        elif purpose == 'promotion' or case.split == 'golden':
            available.append(case)
    return available, future


def score_run(case, run):
    if (case.id, case.role) != (run.case_id, run.role):
        raise ConfigError('eval_case_identity_mismatch')
    annotations = {a.check_id: a for a in run.output.checks} if run.output else {}
    if set(annotations) - {c.id for c in case.expected.checks}:
        raise ConfigError('unknown_check')
    findings = (compare_findings(case, run.output.observed_defects) if run.output else
                dict(passed=False, missed_defects=case.expected.known_defects, false_positives=[]))
    scores = []
    for check in case.expected.checks:
        a = annotations.get(check.id)
        state = run.status; reason = 'run_' + state
        if state == 'passed':
            if a is None:
                state = 'not_run'; reason = 'annotation_missing'
            elif a.annotation_kind == 'llm':
                # No calibrated judge is delivered. LLM annotations never satisfy the gate.
                state = 'blocked'; reason = 'calibrated_judge_unavailable'
            elif check.human_annotation_required and a.annotation_kind != 'human':
                state = 'blocked'; reason = 'human_annotation_required'
            elif check.critical and not findings['passed']:
                state = 'failed'; reason = 'finding_oracle_mismatch'
            else:
                state = a.status; reason = 'artifact_' + state
        scores.append(EvalScore(schema_version=1, run_id=run.run_id, check_id=check.id,
            critical=check.critical, status=state, reason=reason, evidence_ref=run.artifact_ref))
    return scores, findings


def promotion_report(catalog, profiles, runs, *, milestone, purpose):
    if not profiles or len({p.profile_id for p in profiles}) != len(profiles):
        raise ConfigError('duplicate_or_missing_profile')
    controls = {(p.dataset_sha256, p.kit_sha256, p.runtime, canonical(p.tools), p.surface)
                for p in profiles}
    if len(controls) != 1:
        raise ConfigError('incomparable_profiles')
    selected, future = select_cases(catalog, milestone=milestone, purpose=purpose)
    cases = {c.id: c for c in selected}
    by_profile = {sha(canonical(p.model_dump())): p for p in profiles}
    seen = set(); run_ids = set(); evaluated = {}; reports = []
    for run in runs:
        if run.profile_sha256 not in by_profile:
            raise ConfigError('unknown_profile')
        p = by_profile[run.profile_sha256]
        if run.surface != p.surface:
            raise ConfigError('execution_surface_mismatch')
        if run.case_id not in cases:
            all_cases = {c.id: c for c in catalog.cases}
            if run.case_id in all_cases and all_cases[run.case_id].split == 'holdout' and purpose == 'development':
                raise ConfigError('holdout_reserved')
            raise ConfigError('case_outside_milestone')
        if run.repetition > catalog.default_repetitions:
            raise ConfigError('repetition_outside_protocol')
        key = (run.profile_sha256, run.case_id, run.repetition)
        if key in seen or run.run_id in run_ids:
            raise ConfigError('duplicate_repetition')
        seen.add(key); run_ids.add(run.run_id)
        scores, findings = score_run(cases[run.case_id], run)
        evaluated[key] = (run, scores, findings)
    for digest, p in by_profile.items():
        critical = []; other = []; durations = []; rows = []; false_positives = []; missed = []
        simulated = 0
        for case in selected:
            for repetition in range(1, catalog.default_repetitions + 1):
                key = (digest, case.id, repetition)
                if key not in evaluated:
                    rows.append(dict(case_id=case.id, repetition=repetition, status='not_run',
                                     role=case.role, scores=[], reason='capture_missing'))
                    for check in case.expected.checks:
                        (critical if check.critical else other).append(False)
                    continue
                run, scores, findings = evaluated[key]
                # Automation of the target is unsupported. Synthetic/different-surface runs
                # exercise mechanics but cannot be used as model promotion evidence.
                supported = run.mode == 'manual' and not run.simulated and bool(p.configuration_evidence_ref)
                simulated += int(run.simulated)
                if run.duration_ms is not None:
                    durations.append(run.duration_ms)
                false_positives.extend(findings['false_positives']); missed.extend(findings['missed_defects'])
                incomplete = any(s.status in ('blocked', 'not_run') for s in scores)
                passed = supported and all(s.status == 'passed' for s in scores)
                rows.append(dict(case_id=case.id, repetition=repetition, role=case.role,
                    run_id=run.run_id, status='passed' if passed else 'blocked' if not supported or incomplete else run.status if run.status != 'passed' else 'failed',
                    scores=[s.model_dump() for s in scores], simulated=run.simulated,
                    artifact_sha256=run.artifact_sha256, observed_output=run.output.model_dump() if run.output else None))
                for score in scores:
                    (critical if score.critical else other).append(supported and score.status == 'passed')
        pending = sum(row['status'] in ('blocked', 'not_run') for row in rows)
        critical_rate = sum(critical) / len(critical) if critical else 0.0
        other_rate = sum(other) / len(other) if other else 1.0
        allowed = (purpose == 'promotion' and bool(selected) and not pending and
                   critical_rate == 1 and other_rate >= catalog.promotion_gate.noncritical_check_pass_rate_min)
        reports.append(dict(profile_id=p.profile_id, profile_sha256=digest, model=p.model,
            effort=p.effort, surface=p.surface, status='passed' if allowed else 'blocked',
            promotion_allowed=allowed, critical_pass_rate=critical_rate,
            noncritical_pass_rate=other_rate, pending=pending, simulated_runs=simulated,
            false_positives=dict(Counter(false_positives)), missed_defects=dict(Counter(missed)),
            duration_mean_ms=mean(durations) if durations else None,
            duration_variance_ms2=pvariance(durations) if durations else None,
            input_tokens=None, output_tokens=None, cached_tokens=None, cost_usd=None,
            usage_reason='supported_attributable_source_unavailable', matrix=rows))
    allowed = all(r['promotion_allowed'] for r in reports)
    return dict(schema_version=1, command='eval', status='passed' if allowed else 'blocked',
        checks=[], promotion_allowed=allowed, certified=False, evidence_scope='manual_declared',
        purpose=purpose, milestone=milestone, comparable=True, repetitions=catalog.default_repetitions,
        profiles=reports, future_cases=[dict(case_id=c.id, status='not_run') for c in future],
        holdout_policy='promotion_only', publication_allowed=False)
