"""Strict, independent v1 contracts for project integration and observations."""
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .configuration import ConfigError
from .contracts import Contract, Binding, ID
from .onboarding_plan import SHA, canonical, sha, destination_path, separate, unmanaged_path

RoleID = Literal['principal', 'analyst', 'impact-analyzer', 'planner', 'developer', 'tester', 'auditor', 'verifier']
Effort = Literal['low', 'medium', 'high', 'xhigh', 'max', 'ultra']
Text = Annotated[str, Field(min_length=1, max_length=4096)]


class ToolRequirement(Contract):
    id: ID
    kind: Literal['local', 'skill', 'mcp', 'cli']
    purpose: Text
    required: bool


class RoleProfile(Contract):
    id: RoleID
    responsibility: Text
    inputs: Annotated[list[Text], Field(min_length=1, max_length=16)]
    outputs: Annotated[list[Text], Field(min_length=1, max_length=16)]
    write_scope: Literal['assigned-only', 'none']
    sandbox: Literal['read-only', 'workspace-write']
    delegate_when: Text
    max_delegation_depth: int = Field(ge=0, le=1)
    tools: Annotated[list[ToolRequirement], Field(min_length=1, max_length=32)]
    practice_ids: Annotated[list[ID], Field(min_length=1, max_length=32)]
    activated: bool = False
    model: Annotated[str, Field(min_length=1, max_length=128, pattern=r'^[A-Za-z0-9_.-]+$')] | None = None
    effort: Effort | None = None

    @model_validator(mode='after')
    def coherent(self):
        if self.activated != (self.model is not None and self.effort is not None):
            raise ValueError('explicit profile required')
        if not self.activated and (self.model is not None or self.effort is not None):
            raise ValueError('inactive profile has model')
        if self.write_scope == 'none' and self.sandbox != 'read-only':
            raise ValueError('reviewer sandbox')
        if len({t.id for t in self.tools}) != len(self.tools):
            raise ValueError('duplicate tool')
        return self


class RoleCatalog(Contract):
    catalog_version: Literal['1.0.0'] = '1.0.0'
    practice_pack_version: str
    max_concurrent: int = Field(ge=1, le=4)
    roles: Annotated[list[RoleProfile], Field(min_length=8, max_length=8)]

    @model_validator(mode='after')
    def unique(self):
        if len({r.id for r in self.roles}) != 8:
            raise ValueError('all eight roles required')
        return self

    @property
    def sha256(self):
        return sha(canonical(self.model_dump()))


class RoleAssignment(Contract):
    role: RoleID
    write_paths: Annotated[list[str], Field(max_length=64)]
    isolation: ID
    delegation_depth: int = Field(ge=0, le=1, default=0)

    @model_validator(mode='after')
    def paths(self):
        for path in self.write_paths:
            destination_path(path.rstrip('/'))
        return self


def activate_profiles(catalog, selected, available_models):
    """Availability is a selected-account input, never inferred from file presence."""
    roles = {r.id: r for r in catalog.roles}
    if not selected or not set(selected) <= set(roles):
        raise ConfigError('invalid_role_selection')
    data = catalog.model_dump()
    for role in data['roles']:
        role.update(activated=False, model=None, effort=None)
        if role['id'] not in selected:
            continue
        profile = selected[role['id']]
        if set(profile) != {'model', 'effort'}:
            raise ConfigError('invalid_profile')
        if profile['model'] not in available_models:
            raise ConfigError('model_unavailable')
        if profile['effort'] not in available_models[profile['model']]:
            raise ConfigError('effort_unavailable')
        role.update(activated=True, **profile)
    try:
        return RoleCatalog.model_validate(data)
    except ValueError:
        raise ConfigError('invalid_profile') from None


def check_assignments(catalog, assignments):
    if len(assignments) > catalog.max_concurrent:
        raise ConfigError('delegation_limit')
    claimed = []
    roles = {r.id: r for r in catalog.roles}
    for assignment in assignments:
        role = roles[assignment.role]
        if not role.activated:
            raise ConfigError('role_inactive')
        if assignment.delegation_depth > role.max_delegation_depth:
            raise ConfigError('delegation_limit')
        if assignment.write_paths and role.write_scope == 'none':
            raise ConfigError('read_only_assignment')
        for path in assignment.write_paths:
            path = path.rstrip('/').lower()
            for isolation, other in claimed:
                if isolation == assignment.isolation and (path == other or path.startswith(other + '/') or other.startswith(path + '/')):
                    raise ConfigError('writer_collision')
            claimed.append((assignment.isolation, path))


class IntegrationEdit(Contract):
    path: str
    owner: Literal['harness-desktop-v1'] = 'harness-desktop-v1'
    content: Annotated[str, Field(max_length=128 * 1024)]
    old_hash: SHA | None
    old_identity: str | None
    new_hash: SHA
    backup: str | None

    @model_validator(mode='after')
    def valid(self):
        destination_path(self.path)
        if len(self.content.encode('utf-8')) > 128 * 1024 or sha(self.content.encode('utf-8')) != self.new_hash:
            raise ValueError('new hash')
        if (self.old_hash is None) != (self.old_identity is None) or (self.old_hash is None) != (self.backup is None):
            raise ValueError('backup required for edits')
        if self.backup is not None:
            destination_path(self.backup)
        return self


class DesktopIntegrationPlan(Contract):
    kind: Literal['desktop_integration_plan'] = 'desktop_integration_plan'
    run_id: ID
    target_path: str
    target_identity: str
    policy_path: str
    binding_path: str
    binding: Binding
    input_hashes: dict[str, SHA]
    catalog: RoleCatalog
    resource_sha256: SHA
    edits: Annotated[list[IntegrationEdit], Field(min_length=1, max_length=16)]
    plan_sha256: SHA

    @model_validator(mode='after')
    def valid(self):
        separate([self.target_path, self.policy_path, self.binding_path, self.binding.state_dir])
        unmanaged_path(self.target_path)
        unmanaged_path(self.binding.state_dir)
        if len({e.path.lower() for e in self.edits}) != len(self.edits):
            raise ValueError('duplicate paths')
        if sha(canonical(self.model_dump(exclude={'plan_sha256'}))) != self.plan_sha256:
            raise ValueError('plan integrity')
        return self


class IntegrationRecord(Contract):
    path: str
    kind: Literal['file', 'directory']
    identity: str
    state: Literal['prepared', 'applied', 'recovered', 'conflict']


class IntegrationJournal(Contract):
    kind: Literal['desktop_integration_journal'] = 'desktop_integration_journal'
    client_id: ID
    checkout_id: ID
    plan_sha256: SHA
    target_identity: str
    state: Literal['prepared', 'applied', 'failed', 'recovered', 'conflict']
    records: Annotated[list[IntegrationRecord], Field(max_length=64)]


class DesktopObservation(Contract):
    role: RoleID
    surface: Annotated[str, Field(min_length=1, max_length=128)]
    status: Literal['observed', 'unsupported', 'not_checked', 'unavailable', 'conflict']
    source: Literal['desktop', 'cli', 'files'] = 'desktop'
    evidence_ref: ID
    model: str | None = None
    effort: Effort | None = None
    effective_sandbox: Literal['read-only', 'workspace-write', 'unrestricted'] | None = None


class DesktopCertificate(Contract):
    kind: Literal['desktop_certificate'] = 'desktop_certificate'
    catalog_sha256: SHA
    app_version: Annotated[str, Field(min_length=1, max_length=128)]
    engine_version: Annotated[str, Field(min_length=1, max_length=128)]
    account_ref: ID
    observations: Annotated[list[DesktopObservation], Field(max_length=256)]

    @model_validator(mode='after')
    def unique(self):
        keys = [(o.role, o.surface) for o in self.observations]
        if len(keys) != len(set(keys)):
            raise ValueError('duplicate observation')
        return self


def assess_certificate(catalog, certificate):
    if certificate.catalog_sha256 != catalog.sha256:
        raise ConfigError('certificate_catalog_mismatch')
    observations = {(o.role, o.surface): o for o in certificate.observations}
    checks = []
    active = [r for r in catalog.roles if r.activated]
    for role in active:
        expected = {'role', 'model-effort', 'skill:harness-hu', 'permissions'}
        required_tools = {'tool:' + t.id for t in role.tools if t.required}
        expected |= {'tool:' + t.id for t in role.tools}
        expected |= {o.surface for o in certificate.observations if o.role == role.id and o.surface.startswith('hook:')}
        for surface in sorted(expected):
            required = surface in {'role', 'model-effort', 'skill:harness-hu', 'permissions'} | required_tools
            observed = observations.get((role.id, surface))
            status = 'not_checked' if observed is None or observed.source != 'desktop' else observed.status
            if status == 'observed' and surface == 'model-effort' and (observed.model, observed.effort) != (role.model, role.effort):
                status = 'conflict'
            if status == 'observed' and surface == 'permissions' and observed.effective_sandbox != role.sandbox:
                status = 'conflict'
            checks.append(dict(id=role.id + ':' + surface, status=status, required=required,
                evidence_ref=observed.evidence_ref if observed else None))
    blocked = any(c['required'] and c['status'] in ('conflict', 'unsupported', 'unavailable') for c in checks)
    certified = bool(active) and all(c['status'] == 'observed' for c in checks if c['required'])
    return dict(schema_version=1, command='desktop-check', status='blocked' if blocked else ('ready' if certified else 'partial'),
                certified=certified, desktop_status='observed' if certified else 'not_checked', checks=checks)
