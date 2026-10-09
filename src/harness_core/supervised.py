"""Supervised acceptance never relaxes the strict Desktop certificate."""
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .contracts import Contract, ID
from .configuration import ConfigError, reject_secrets
from .desktop import assess_certificate
from .onboarding_plan import SHA, canonical, sha, destination_path, unmanaged_path


class CandidateEntry(Contract):
    path: str
    kind: Literal['file', 'directory', 'absent']
    identity: str | None
    content_sha256: SHA | None

    @model_validator(mode='after')
    def valid(self):
        destination_path(self.path)
        if (self.kind == 'file') != (self.content_sha256 is not None):
            raise ValueError('file hash required')
        if (self.kind == 'absent') != (self.identity is None):
            raise ValueError('entry identity required')
        return self


class CandidateSnapshot(Contract):
    kind: Literal['candidate_snapshot'] = 'candidate_snapshot'
    client_id: ID
    checkout_id: ID
    target_path: str
    target_identity: str
    catalog_sha256: SHA
    evidence_sha256: SHA
    configuration_sha256: SHA
    scopes: Annotated[list[str], Field(min_length=1, max_length=32)]
    entries: Annotated[list[CandidateEntry], Field(min_length=1, max_length=256)]

    @model_validator(mode='after')
    def valid(self):
        unmanaged_path(self.target_path)
        for scope in self.scopes:
            destination_path(scope)
        if len({p.lower() for p in self.scopes}) != len(self.scopes):
            raise ValueError('duplicate scope')
        if len({e.path.lower() for e in self.entries}) != len(self.entries):
            raise ValueError('duplicate entry')
        for entry in self.entries:
            if not any(entry.path == s or entry.path.startswith(s + '/') for s in self.scopes):
                raise ValueError('entry outside scope')
        if not all(any(e.path == s for e in self.entries) for s in self.scopes):
            raise ValueError('missing scope entry')
        return self

    @property
    def sha256(self):
        return sha(canonical(self.model_dump()))


class SupervisedAcceptance(Contract):
    kind: Literal['supervised_acceptance'] = 'supervised_acceptance'
    client_id: ID
    checkout_id: ID
    catalog_sha256: SHA
    candidate_sha256: SHA
    evidence_sha256: SHA
    operator_ref: ID
    accepted: bool
    limitations: Annotated[list[str], Field(max_length=256)]


def evidence_digest(certificate):
    reject_secrets(certificate.model_dump())
    return sha(canonical(certificate.model_dump()))


def assess_preparation(catalog, certificate, snapshot, acceptance, *, required=()):
    if snapshot.catalog_sha256 != catalog.sha256 or snapshot.evidence_sha256 != evidence_digest(certificate):
        raise ConfigError('supervised_evidence_mismatch')
    strict = assess_certificate(catalog, certificate)
    limitations = [c['id'] for c in strict['checks'] if c['status'] != 'observed']
    identity_ok = acceptance is not None and acceptance.accepted and (
        acceptance.client_id, acceptance.checkout_id, acceptance.catalog_sha256,
        acceptance.candidate_sha256, acceptance.evidence_sha256) == (
        snapshot.client_id, snapshot.checkout_id, snapshot.catalog_sha256,
        snapshot.sha256, snapshot.evidence_sha256)
    acceptance_ok = identity_ok and set(limitations) <= set(acceptance.limitations)
    # Files/CLI claims of role execution cannot prepare a supervised workflow.
    roles = {c['id']: c['status'] for c in strict['checks']}
    discovery_ok = any(r.activated for r in catalog.roles) and all(
        roles.get(r.id + ':role') == 'observed' for r in catalog.roles if r.activated)
    blocked_required = [key for key in required if roles.get(key) != 'observed']
    prepared = bool(acceptance_ok and discovery_ok and not blocked_required)
    return dict(schema_version=1, command='supervised-prepare', status='ready' if prepared else 'blocked',
        prepared=prepared, mode='supervised', certified=strict['certified'],
        candidate_sha256=snapshot.sha256, evidence_sha256=snapshot.evidence_sha256,
        limitations=limitations, blocked_required=blocked_required, strict_certificate=strict,
        checks=[dict(id='operator-acceptance', status='observed' if acceptance_ok else 'conflict'),
                dict(id='role-discovery', status='observed' if discovery_ok else 'not_checked')])
