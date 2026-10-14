"""Independent setup v1 contracts; published client contracts are unchanged."""
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AfterValidator, Field, model_validator

from .configuration import ConfigError, normalize_remote
from .contracts import ID, Binding, Descriptor, Policy
from .guided import SafeContract, Text, GuidedRequest
from .onboarding_plan import SHA, Operation, absolute_path, canonical, denied, destination_path, sha


def scope_path(value):
    destination_path(value.removesuffix('/'))
    return value


ScopePath = Annotated[Text, AfterValidator(scope_path)]
Capability = Literal['local', 'git', 'openspec', 'databricks', 'desktop']
Reason = Literal['invalid_input', 'identity_mismatch', 'access_denied', 'tool_unavailable',
    'download_integrity_failed', 'skill_discovery_pending', 'auth_pending', 'permission_conflict',
    'plan_stale', 'owned_resource_conflict', 'recovery_required', 'remote_not_checked']


def unique_paths(paths):
    # Windows path spelling is preserved for handle-relative alias checks.
    if len({p.casefold().rstrip('/') for p in paths}) != len(paths):
        raise ValueError('duplicate_path_alias')


class AccessScope(SafeContract):
    kind: Literal['access_scope'] = 'access_scope'
    client_id: ID
    policy_sha256: SHA
    read_allow: list[ScopePath] = Field(max_length=256)
    write_allow: list[ScopePath] = Field(max_length=256)
    deny: list[ScopePath] = Field(max_length=256)

    @model_validator(mode='after')
    def paths(self):
        for paths in (self.read_allow, self.write_allow, self.deny): unique_paths(paths)
        return self


class InstalledTool(SafeContract):
    name: ID
    version: Text
    path: Text
    sha256: SHA
    license: Text

    @model_validator(mode='after')
    def absolute(self):
        absolute_path(self.path)
        return self


class InstallationRecord(SafeContract):
    kind: Literal['installation_record'] = 'installation_record'
    version: Text
    product_sha256: SHA
    installation_root: Text
    runtime_path: Text
    skill_path: Text
    skill_sha256: SHA | None = None
    skill_files: dict[ScopePath,SHA] = Field(default_factory=dict)
    kit_path: Text | None = None
    tools: list[InstalledTool] = Field(max_length=32)
    owned_files: dict[ScopePath, SHA]
    resource_installed: bool
    skill_discovered: bool
    certified: Literal[False] = False
    release_allowed: Literal[False] = False

    @model_validator(mode='after')
    def ownership(self):
        root=absolute_path(self.installation_root)
        if not absolute_path(self.runtime_path).is_relative_to(root):
            raise ValueError('runtime_outside_installation')
        absolute_path(self.skill_path)
        unique_paths(self.owned_files)
        if len(self.owned_files)>20000 or len({t.name for t in self.tools})!=len(self.tools):
            raise ValueError('invalid_ownership')
        if self.skill_discovered and not self.resource_installed:
            raise ValueError('discovery_requires_resource')
        if self.resource_installed and not self.skill_sha256:
            raise ValueError('skill_hash_required')
        return self


class SetupInput(SafeContract):
    kind: Literal['setup_input'] = 'setup_input'
    descriptor: Descriptor
    policy: Policy
    binding: Binding
    repository_url: Text | None = None
    access_scope: AccessScope
    capabilities: list[Capability] = Field(min_length=1,max_length=5)
    sources: dict[Literal['descriptor','policy','binding','repository_url','access_scope','capabilities'],
                  Literal['file','user','local','template']]
    guided_request: GuidedRequest | None = None
    clone: bool = False
    commit_local: bool = False
    remote_read: bool = False
    databricks_host: Text | None = None
    installation_record: Text | None = None
    installation_kit: Text | None = None

    @model_validator(mode='after')
    def identity(self):
        d,p,b,a=self.descriptor,self.policy,self.binding,self.access_scope
        if len({d.client_id,p.client_id,b.client_id,a.client_id})!=1:
            raise ValueError('identity_mismatch')
        if d.repository.casefold()!=p.repository.casefold() or d.base_branch!=p.base_branch:
            raise ValueError('identity_mismatch')
        if self.repository_url and normalize_remote(self.repository_url)!=d.repository.casefold():
            raise ValueError('identity_mismatch')
        if a.policy_sha256!=b.policy_sha256:
            raise ValueError('policy_hash_mismatch')
        target=absolute_path(b.target_path)
        state=absolute_path(b.state_dir)
        if state.is_relative_to(target) or target.is_relative_to(state) or tuple(state.parts[-2:])!=(b.client_id,b.checkout_id):
            raise ValueError('state_path_invalid')
        if len(set(self.capabilities))!=len(self.capabilities):
            raise ValueError('duplicate_capability')
        if self.guided_request:
            r=self.guided_request
            if (absolute_path(r.target_path)!=target or r.tool_binding.client_id!=d.client_id or r.tool_binding.checkout_id!=b.checkout_id
                or r.development.client_id!=d.client_id or r.repository not in (None,d.repository) or r.base_branch not in (None,d.base_branch)):
                raise ValueError('identity_mismatch')
        if self.databricks_host:
            from urllib.parse import urlsplit
            host=urlsplit(self.databricks_host)
            if (host.scheme!='https' or not host.hostname or host.path not in ('','/') or host.port not in (None,443)
                or host.username or host.password or host.query or host.fragment):
                raise ValueError('invalid_host')
        if self.clone and not self.repository_url: raise ValueError('clone_url_required')
        if self.remote_read and ('databricks' not in self.capabilities or not self.binding.databricks_profile or not self.databricks_host):
            raise ValueError('remote_selection_required')
        return self


class SetupEffect(SafeContract):
    kind: Literal['download','install','clone','create','integrate','auth','read','local_commit']
    destination: Text
    description: Text
    artifact_sha256: SHA | None = None


class SetupStage(SafeContract):
    name: Literal['validate','tools','checkout','prepare','integrate','auth','check','report']
    dependencies: list[Text]
    child_sha256: SHA | None = None
    status: Literal['pending','completed','blocked','failed','recovered'] = 'pending'
    reason: Reason | None = None


class SetupPlan(SafeContract):
    kind: Literal['setup_plan'] = 'setup_plan'
    run_id: ID
    inputs: SetupInput
    input_hashes: dict[Text,SHA]
    child_plans: dict[Text,SHA]
    child_payloads: dict[Text,str] = Field(default_factory=dict)
    setup_operations: list[Operation] = Field(default_factory=list,max_length=1)
    stages: list[SetupStage] = Field(max_length=8)
    technical_reads: list[ScopePath] = Field(max_length=256)
    integration_writes: list[ScopePath] = Field(max_length=256)
    effects: list[SetupEffect] = Field(max_length=256)
    applicable: bool
    blockers: list[Reason] = Field(max_length=32)
    plan_sha256: SHA

    @model_validator(mode='after')
    def integrity(self):
        for paths in (self.technical_reads,self.integration_writes):
            unique_paths(paths)
            if any(p.endswith('/') for p in paths): raise ValueError('exact_technical_paths_required')
        names=[s.name for s in self.stages]
        if len(names)!=len(set(names)): raise ValueError('duplicate_stage')
        prior=set()
        if set(self.child_payloads)!=set(self.child_plans): raise ValueError('child_hash_mismatch')
        for name,content in self.child_payloads.items():
            if sha(content.encode('utf-8'))!=self.child_plans.get(name): raise ValueError('child_hash_mismatch')
        if 'onboarding' in self.child_payloads:
            import json
            from .guided import GuidedOnboardingPlan
            child=GuidedOnboardingPlan.model_validate(json.loads(self.child_payloads['onboarding']))
            if child.request!=self.inputs.guided_request or child.preparation.binding!=self.inputs.binding:
                raise ValueError('child_identity_mismatch')
            writes={o.path for o in child.preparation.operations if o.scope=='target'} | {e.path for e in child.integration_edits}
            if writes|{o.path for o in self.setup_operations}!=set(self.integration_writes): raise ValueError('child_scope_mismatch')
        for op in self.setup_operations:
            if op.scope!='target' or op.path!='.harness/access-scope.json' or op.content!=(canonical(self.inputs.access_scope.model_dump())+b'\n').decode():
                raise ValueError('invalid_setup_operation')
        for stage in self.stages:
            if not set(stage.dependencies)<=prior: raise ValueError('invalid_stage_dependency')
            prior.add(stage.name)
            if stage.child_sha256 and stage.child_sha256 not in self.child_plans.values():
                raise ValueError('child_hash_mismatch')
        if self.applicable!= (not self.blockers): raise ValueError('invalid_applicability')
        if sha(canonical(self.model_dump(exclude={'plan_sha256'})))!=self.plan_sha256:
            raise ValueError('plan_hash_mismatch')
        return self


class CapabilityEvidence(SafeContract):
    identity: Text
    version: Text
    observed_at: Text
    valid_until: Text
    evidence_path: Text
    evidence_sha256: SHA
    source: Literal['local_test','local_probe','desktop','remote_read']

    @model_validator(mode='after')
    def validity(self):
        from datetime import datetime
        start,end=map(datetime.fromisoformat,(self.observed_at,self.valid_until))
        if start.tzinfo is None or end.tzinfo is None or start>=end: raise ValueError('invalid_evidence_validity')
        return self


class CapabilityResult(SafeContract):
    id: Capability
    status: Literal['available','blocked','not_checked','unsupported']
    reason: Reason | None = None
    next_action: Text | None = None
    evidence: list[CapabilityEvidence] = Field(max_length=64)

    @model_validator(mode='after')
    def observed(self):
        if self.status=='available' and not self.evidence: raise ValueError('available_requires_evidence')
        if self.status!='available' and self.reason is None: raise ValueError('reason_required')
        if self.id=='desktop' and self.status=='available' and not any(e.source=='desktop' for e in self.evidence):
            raise ValueError('desktop_observation_required')
        if self.id=='databricks' and self.status=='available' and not any(e.source=='remote_read' for e in self.evidence):
            raise ValueError('remote_observation_required')
        return self


class SetupReport(SafeContract):
    kind: Literal['setup_report'] = 'setup_report'
    client_id: ID
    checkout_id: ID
    plan_sha256: SHA
    prepared: bool
    stages: list[SetupStage] = Field(max_length=8)
    capabilities: list[CapabilityResult] = Field(max_length=5)
    hu_admissible: list[Literal['local_prepared','local_clean','remote_validation']] = Field(default_factory=list)
    certified: Literal[False] = False
    release_allowed: Literal[False] = False
    publication_allowed: Literal[False] = False

    @model_validator(mode='after')
    def unique(self):
        if len({c.id for c in self.capabilities})!=len(self.capabilities): raise ValueError('duplicate_capability')
        return self


MODELS=(InstallationRecord,SetupInput,AccessScope,SetupPlan,SetupReport)


def within(path, entries):
    """An explicit trailing slash permits descendants, never sibling prefixes."""
    return any(path.casefold()==p.casefold() if not p.endswith('/') else
               path.casefold().startswith(p.casefold()) for p in entries)


def authorize_access(scope, policy, path, operation, plan_paths, *, read_required=False):
    destination_path(path)
    if operation not in ('read','write'):
        raise ConfigError('invalid_input')
    if scope.client_id!=policy.client_id:
        raise ConfigError('identity_mismatch')
    for p in plan_paths: scope_path(p)
    if (not within(path,plan_paths) or within(path,scope.deny) or denied(path,policy.denied_paths)
        or not within(path,scope.read_allow if operation=='read' else scope.write_allow)
        or (operation=='write' and (denied(path,policy.read_only_paths) or
            (read_required and not within(path,scope.read_allow))))):
        raise ConfigError('access_denied')
    return path
