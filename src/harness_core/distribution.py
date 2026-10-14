"""Distribution contracts are independent of init/onboarding v1."""
from typing import Literal

from pydantic import Field, model_validator

from .contracts import ID
from .guided import SafeContract, Text
from .onboarding_plan import SHA, canonical, sha, destination_path
from .configuration import ConfigError


class PinnedDependency(SafeContract):
    name: Text
    version: Text
    sha256: SHA
    license: Text
    artifact: Text


class PinnedSource(SafeContract):
    name: Text
    commit: str = Field(pattern=r'^[a-f0-9]{40}$')
    sha256: SHA
    license: Text


class ReleaseManifest(SafeContract):
    kind: Literal['release_candidate'] = 'release_candidate'
    version: Text
    base_commit: str = Field(pattern=r'^[a-f0-9]{40}$')
    resources: dict[str, SHA]
    dependencies: list[PinnedDependency] = Field(min_length=1, max_length=32)
    sources: list[PinnedSource] = Field(min_length=1, max_length=32)
    certified: Literal[False] = False
    release_allowed: Literal[False] = False
    pending_acceptance: list[Text] = Field(min_length=1, max_length=64)
    manifest_sha256: SHA

    @model_validator(mode='after')
    def integrity(self):
        for path in self.resources: destination_path(path)
        if not self.resources or sha(canonical(self.model_dump(exclude={'manifest_sha256'}))) != self.manifest_sha256:
            raise ValueError('release_manifest_hash_mismatch')
        return self


class InstallationBinding(SafeContract):
    binding_path: Text
    release_sha256: SHA
    files: dict[str, SHA]

    @model_validator(mode='after')
    def ownership(self):
        for path in self.files:
            managed_destination(path)
        if len(self.files) > 64 or len({p.casefold() for p in self.files}) != len(self.files):
            raise ValueError('duplicate_ownership')
        return self


def managed_destination(path):
    destination_path(path)
    if path.casefold() == 'kit.lock.json' or path.split('/')[0].casefold() in {'.git', '.harness'}:
        raise ConfigError('update_destination_denied')
    return path


class UpdateEdit(SafeContract):
    path: Text
    content: str = Field(max_length=128*1024)
    installed_hash: SHA | None
    local_hash: SHA | None
    local_identity: str | None
    upstream_hash: SHA
    backup: str | None
    conflict: bool

    @model_validator(mode='after')
    def integrity(self):
        destination_path(self.path)
        if len(self.content.encode('utf-8')) > 128*1024:
            raise ValueError('update_content_too_large')
        if sha(self.content.encode('utf-8')) != self.upstream_hash:
            raise ValueError('update_content_hash_mismatch')
        if self.conflict != (self.local_hash != self.installed_hash):
            raise ValueError('update_conflict_mismatch')
        return self


class UpdatePlan(SafeContract):
    kind: Literal['update_plan'] = 'update_plan'
    run_id: ID
    target_path: Text
    target_identity: Text
    policy_path: Text
    binding_path: Text
    input_hashes: dict[str, SHA]
    installation: InstallationBinding
    manifest: ReleaseManifest
    edits: list[UpdateEdit] = Field(min_length=1, max_length=65)
    applicable: bool
    plan_sha256: SHA

    @model_validator(mode='after')
    def integrity(self):
        if len({e.path.casefold() for e in self.edits}) != len(self.edits):
            raise ValueError('duplicate_edits')
        if self.applicable != (not any(e.conflict for e in self.edits)):
            raise ValueError('update_applicability_mismatch')
        if sha(canonical(self.model_dump(exclude={'plan_sha256'}))) != self.plan_sha256:
            raise ValueError('update_plan_hash_mismatch')
        return self


class UpdateRequest(SafeContract):
    installation: InstallationBinding
    manifest: ReleaseManifest
    upstream: dict[str, str]


class UpdateRecord(SafeContract):
    path: Text
    identity: Text
    state: Literal['prepared', 'applied', 'recovered']


class UpdateJournal(SafeContract):
    plan_sha256: SHA
    target_identity: Text
    state: Literal['prepared', 'applied', 'failed', 'recovered']
    records: list[UpdateRecord]


PROTOCOLS = ('predecessor_evals', 'compatible_sandbox', 'harness_publication',
    'alpha_hu', 'beta_hu', 'client_isolation', 'synthetic_client_pilot',
    'interrupt_resume', 'update_recover', 'second_environment', 'new_user_desktop')


class PilotReceipt(SafeContract):
    protocol: Literal[*PROTOCOLS]
    status: Literal['not_run', 'blocked', 'passed', 'failed']
    source: Literal['desktop_harness', 'local_test', 'simulated', 'manual_git']
    evidence_path: Text
    evidence_sha256: SHA


class PilotReport(SafeContract):
    candidate_sha256: SHA
    implementation_status: Literal['not_started', 'partial', 'complete']
    receipts: list[PilotReceipt] = Field(max_length=11)
    evaluation_path: Text | None = None
    evaluation_sha256: SHA | None = None
    catalog_path: Text | None = None
    catalog_sha256: SHA | None = None
    certificate_path: Text | None = None
    certificate_sha256: SHA | None = None
    configuration_evidence: dict[str, SHA] = Field(default_factory=dict)

    @model_validator(mode='after')
    def unique(self):
        if len({r.protocol for r in self.receipts}) != len(self.receipts):
            raise ValueError('duplicate_protocol')
        return self


MODELS = (ReleaseManifest, InstallationBinding, UpdatePlan, UpdateRequest, UpdateJournal, PilotReport)
