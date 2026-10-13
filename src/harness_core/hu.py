"""Independent HU v1 contracts; no changes to onboarding or Desktop v1."""
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .contracts import ID
from .guided import SafeContract, Text, Texts
from .desktop import RoleAssignment, RoleCatalog
from .onboarding_plan import SHA, canonical, sha, destination_path

State = Literal['draft', 'analyzing', 'planned', 'approved', 'implementing', 'validating',
    'reviewing', 'ready_to_publish', 'published', 'failed', 'cancelled']


class Empty(SafeContract):
    pass


class Start(Empty):
    onboarding_plan: Text
    writer_actor: ID
    simulation: bool = False


class PlanInput(Empty):
    criteria: Annotated[Texts, Field(min_length=1)]
    paths: Annotated[list[str], Field(min_length=1, max_length=64)]
    operations: Annotated[list[Literal['create', 'modify', 'delete']], Field(min_length=1, max_length=3)]
    tests: Annotated[list[ID], Field(min_length=1, max_length=64)]
    required_capabilities: list[ID] = Field(default_factory=list, max_length=64)
    max_delegations: int = Field(default=2, ge=0, le=4)
    allow_worktrees: bool = False
    sources: dict[ID, Literal['user', 'local', 'template']] = Field(default_factory=dict)
    decisions: Texts = Field(default_factory=list)

    @model_validator(mode='after')
    def scope(self):
        for path in self.paths: destination_path(path.rstrip('/'))
        for values in (self.paths, self.operations, self.tests, self.required_capabilities):
            if len(set(v.lower() for v in values)) != len(values): raise ValueError('duplicate scope')
        return self


class PlanRevision(PlanInput):
    revision: int = Field(ge=1)
    context_sha256: SHA
    plan_sha256: SHA

    @model_validator(mode='after')
    def integrity(self):
        if sha(canonical(self.model_dump(exclude={'plan_sha256'}))) != self.plan_sha256:
            raise ValueError('plan integrity')
        return self


class Approval(Empty):
    actor: ID
    confirmed: bool
    client_id: ID
    checkout_id: ID
    attempt: int = Field(ge=1)
    revision: int = Field(ge=1)
    plan_sha256: SHA


class ApprovalRecord(Approval):
    approved_at: Text


class CandidateEntry(Empty):
    path: str
    operation: Literal['create', 'modify', 'delete']
    base_oid: str | None
    content_sha256: SHA | None
    index_oid: str | None
    index_mode: str | None
    staged_operation: Literal['create','modify','delete'] | None

    @model_validator(mode='after')
    def valid(self):
        destination_path(self.path)
        if (self.operation == 'delete') != (self.content_sha256 is None): raise ValueError('candidate content')
        return self


class Candidate(Empty):
    base: str
    baseline_sha256: SHA
    context_sha256: SHA
    plan_sha256: SHA
    entries: list[CandidateEntry] = Field(max_length=256)
    candidate_sha256: SHA

    @model_validator(mode='after')
    def integrity(self):
        if sha(canonical(self.model_dump(exclude={'candidate_sha256'}))) != self.candidate_sha256:
            raise ValueError('candidate integrity')
        return self


class Evidence(Empty):
    id: ID
    candidate_sha256: SHA
    status: Literal['passed', 'failed', 'blocked', 'not_run', 'unavailable']
    simulated: bool
    actor: ID
    kind: Literal['test', 'review', 'capability']
    evidence_ref: ID


class Assignment(RoleAssignment):
    actor: ID


class Transition(Empty):
    state: State


class Block(Empty):
    reason: ID


class Handoff(Empty):
    role: Literal['principal', 'analyst', 'impact-analyzer', 'planner', 'developer', 'tester', 'auditor', 'verifier']
    actor: ID
    plan_sha256: SHA
    candidate_sha256: SHA | None = None
    sources: dict[ID, Literal['user', 'local', 'template']]
    decisions: Texts
    findings: Texts
    status: Literal['completed', 'blocked', 'not_run']


class WorktreeInput(Empty):
    path: Text
    branch: ID
    confirmed: bool


class WorktreeRecord(WorktreeInput):
    target_identity: Text
    base: str


class GateResult(Empty):
    gate: ID
    status: Literal['passed', 'blocked', 'partial', 'not_checked']
    reason: ID | None = None
    candidate_sha256: SHA | None = None


class HuRun(Empty):
    kind: Literal['hu_run'] = 'hu_run'
    story_id: ID
    run_id: ID
    client_id: ID
    checkout_id: ID
    target_identity: Text
    onboarding_plan: Text
    writer_actor: ID
    catalog: RoleCatalog
    attempt: int = Field(default=1, ge=1)
    state: State = 'draft'
    simulation: bool
    context_sha256: SHA
    base: str
    baseline_files: dict[str, SHA] = Field(default_factory=dict, max_length=4096)
    plan: PlanRevision | None = None
    approval: ApprovalRecord | None = None
    candidate: Candidate | None = None
    evidence: list[Evidence] = Field(default_factory=list, max_length=256)
    assignments: list[Assignment] = Field(default_factory=list, max_length=4)
    handoffs: list[Handoff] = Field(default_factory=list, max_length=128)
    corrections: int = Field(default=0, ge=0, le=2)
    delegations: int = Field(default=0, ge=0, le=4)
    blocked_reason: ID | None = None
    worktrees: list[WorktreeRecord] = Field(default_factory=list, max_length=4)


INPUTS = dict(start=Start, plan=PlanInput, approve=Approval, candidate=Empty, evidence=Evidence,
    assign=Assignment, transition=Transition, block=Block, correct=Empty, resume=Empty,
    handoff=Handoff, worktree=WorktreeInput, attempt=Empty)


def covers(path, scopes):
    path = path.lower()
    return any(path == scope.rstrip('/').lower() or path.startswith(scope.rstrip('/').lower() + '/') for scope in scopes)


def approval_current(run):
    a, p = run.approval, run.plan
    return bool(a and p and a.confirmed and (a.client_id, a.checkout_id, a.attempt, a.revision, a.plan_sha256) ==
        (run.client_id, run.checkout_id, run.attempt, p.revision, p.plan_sha256) and p.context_sha256 == run.context_sha256)


def evidence_gate(run, kind, ids):
    if not run.candidate: return 'candidate_required'
    records = {e.id: e for e in run.evidence if e.kind == kind}
    for key in ids:
        e = records.get(key)
        if not e or e.status != 'passed': return 'evidence_required'
        if e.candidate_sha256 != run.candidate.candidate_sha256: return 'stale_evidence'
        if e.simulated and not run.simulation: return 'simulated_evidence'
        writers = {a.actor for a in run.assignments if a.write_paths}
        writers.add(run.writer_actor)
        writers.update(h.actor for h in run.handoffs if h.role in ('principal','developer','tester'))
        writers.update(e.actor for e in run.evidence if e.kind=='test')
        if kind == 'review' and e.actor in writers: return 'independent_review_required'
    return None
