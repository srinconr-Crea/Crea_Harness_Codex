"""Independent story/publication v1 contracts. External prose is always data."""
from typing import Annotated, Literal, Protocol

from pydantic import Field, model_validator

from .contracts import ID, Repo, Branch
from .guided import SafeContract, Text
from .onboarding_plan import SHA, canonical, sha

OID = Annotated[str, Field(pattern=r'^[a-f0-9]{40}$')]
Capability = Literal['read_story', 'create_branch', 'push', 'create_pr', 'write_story']


class ProviderBinding(SafeContract):
    client_id: ID
    checkout_id: ID
    provider: Literal['fixture', 'github']
    transport: Literal['fixture', 'cli', 'mcp']
    host: Literal['github.com'] = 'github.com'
    repository: Repo
    base_branch: Branch
    capabilities: list[Capability] = Field(min_length=1, max_length=5)

    @model_validator(mode='after')
    def selection(self):
        if len(set(self.capabilities)) != len(self.capabilities): raise ValueError('duplicate_capability')
        if (self.provider == 'fixture') != (self.transport == 'fixture'): raise ValueError('provider_transport_mismatch')
        return self


class StorySnapshot(SafeContract):
    repository: Repo
    source_id: ID
    revision: Text
    title: Text
    criteria: list[Text] = Field(min_length=1, max_length=64)
    refs: list[Text] = Field(max_length=64)
    trust: Literal['external_data'] = 'external_data'
    acceptance_sha256: SHA
    snapshot_sha256: SHA

    @model_validator(mode='after')
    def integrity(self):
        if self.acceptance_sha256 != sha(canonical(self.criteria)): raise ValueError('acceptance_hash_mismatch')
        if self.snapshot_sha256 != sha(canonical(self.model_dump(exclude={'snapshot_sha256'}))):
            raise ValueError('snapshot_hash_mismatch')
        return self


def snapshot(repository, source_id, revision, title, criteria, refs):
    value = dict(schema_version=1, repository=repository, source_id=source_id, revision=revision,
        title=title, criteria=criteria, refs=refs, trust='external_data', acceptance_sha256=sha(canonical(criteria)))
    return StorySnapshot.model_validate({**value, 'snapshot_sha256': sha(canonical(value))})


def reconcile_story(old, current):
    return None if old == current else 'story_changed'


class PublicationIntent(SafeContract):
    intent_id: ID
    client_id: ID
    checkout_id: ID
    hu_id: ID
    attempt: int = Field(ge=1)
    provider: Literal['fixture', 'github']
    repository: Repo
    base_branch: Branch
    head_branch: Branch
    base_oid: OID
    head_oid: OID
    candidate_sha256: SHA
    context_sha256: SHA
    plan_sha256: SHA
    story: StorySnapshot
    title: Text
    body: Text
    evidence_refs: list[ID] = Field(min_length=1, max_length=256)
    draft: Literal[True] = True
    intent_sha256: SHA

    @model_validator(mode='after')
    def integrity(self):
        if self.story.repository != self.repository or self.base_branch == self.head_branch:
            raise ValueError('publication_identity_mismatch')
        if self.intent_sha256 != sha(canonical(self.model_dump(exclude={'intent_sha256'}))):
            raise ValueError('intent_hash_mismatch')
        if len(set(self.evidence_refs)) != len(self.evidence_refs): raise ValueError('duplicate_evidence')
        return self


def intent(**value):
    value = {**value, 'schema_version': 1, 'draft': True}
    if isinstance(value.get('story'), StorySnapshot): value['story'] = value['story'].model_dump()
    return PublicationIntent.model_validate({**value, 'intent_sha256': sha(canonical(value))})


class PublicationAuthorization(SafeContract):
    actor: ID
    confirmed: bool
    intent_sha256: SHA
    actions: list[Literal['push', 'create_pr']] = Field(max_length=2)

    @model_validator(mode='after')
    def unique(self):
        if len(set(self.actions)) != len(self.actions): raise ValueError('duplicate_action')
        return self


class PublicationReceipt(SafeContract):
    intent: PublicationIntent
    status: Literal['pending', 'unknown', 'pushed', 'published']
    pr_number: int | None = Field(default=None, ge=1)
    pr_url: Text | None = None
    attached: bool = False

    @model_validator(mode='after')
    def identity(self):
        if self.status == 'published':
            expected = f'https://github.com/{self.intent.repository}/pull/{self.pr_number}'
            if not self.pr_number or self.pr_url != expected: raise ValueError('receipt_identity_mismatch')
        elif self.pr_number is not None or self.pr_url is not None or self.attached:
            raise ValueError('unpublished_receipt')
        return self


class StoryPlanBinding(SafeContract):
    client_id: ID
    checkout_id: ID
    hu_id: ID
    attempt: int = Field(ge=1)
    plan_sha256: SHA
    actor: ID
    confirmed: bool
    story: StorySnapshot


MODELS = (ProviderBinding, StorySnapshot, PublicationIntent, PublicationAuthorization, PublicationReceipt, StoryPlanBinding)


class StoryProvider(Protocol):
    simulated: bool
    def read_story(self, binding: ProviderBinding, source_id: str) -> StorySnapshot: ...


class GitProvider(StoryProvider, Protocol):
    def preflight(self, binding: ProviderBinding) -> None: ...
    def branch(self, binding: ProviderBinding, branch: str) -> str | None: ...
    def prs(self, binding: ProviderBinding, intent: PublicationIntent) -> list[dict]: ...
    def push(self, binding: ProviderBinding, intent: PublicationIntent) -> None: ...
    def create_pr(self, binding: ProviderBinding, intent: PublicationIntent) -> dict: ...
