"""Guided onboarding has independent contracts; v1 init remains create-only."""
import re
from typing import Annotated, Any, Literal
from urllib.parse import urlsplit

from pydantic import ConfigDict, Field, model_validator

from .configuration import ConfigError, reject_secrets
from .contracts import Contract, ID, Repo, Branch
from .desktop import RoleID, RoleCatalog, IntegrationEdit
from .onboarding_plan import OnboardingPlan, Operation, SHA, canonical, sha, unmanaged_path, separate
from .supervised import CandidateSnapshot, SupervisedAcceptance
from .desktop import DesktopCertificate
from .onboarding_plan import JournalOperation as OperationRecord


def sanitize(value):
    reject_secrets(value)
    if isinstance(value, dict):
        for item in value.values(): sanitize(item)
    elif isinstance(value, list):
        for item in value: sanitize(item)
    elif isinstance(value, str):
        if re.search(r'(?i)\b(password|token|secret|api[_-]?key)\s*[:=]|\bBearer\s+\S+', value):
            raise ConfigError('secret_not_allowed')
        for url in re.findall(r'[A-Za-z][A-Za-z0-9+.-]*://[^\s]+', value):
            try:
                parsed = urlsplit(url)
                if parsed.username is not None or parsed.password is not None or parsed.query:
                    raise ConfigError('secret_not_allowed')
            except ValueError:
                raise ConfigError('secret_not_allowed') from None


class SafeContract(Contract):
    model_config = ConfigDict(extra='forbid', strict=True, hide_input_in_errors=True)
    @model_validator(mode='before')
    @classmethod
    def no_secrets(cls, value):
        sanitize(value)
        return value


Text = Annotated[str, Field(min_length=1, max_length=4096)]
Texts = Annotated[list[Text], Field(max_length=64)]
Source = Literal['user', 'template', 'local']


class ClientDevelopmentConfig(SafeContract):
    kind: Literal['client_development_config'] = 'client_development_config'
    client_id: ID
    stack: Texts
    conventions: Texts
    business_rules: Texts
    roles: Annotated[list[RoleID], Field(min_length=1, max_length=8)]
    validations: Annotated[list[ID], Field(max_length=64)]
    sources: dict[str, Source]

    @model_validator(mode='after')
    def unique(self):
        if len(set(self.roles)) != len(self.roles) or len(set(self.validations)) != len(self.validations):
            raise ValueError('duplicate selection')
        return self


class ToolConnection(SafeContract):
    id: ID
    kind: Literal['local', 'cli', 'mcp', 'skill']
    connection_ref: ID | None
    status: Literal['declared', 'unavailable', 'not_checked']


class ClientToolBinding(SafeContract):
    kind: Literal['client_tool_binding'] = 'client_tool_binding'
    client_id: ID
    checkout_id: ID
    tools: Annotated[list[ToolConnection], Field(max_length=64)]

    @model_validator(mode='after')
    def unique(self):
        if len({t.id for t in self.tools}) != len(self.tools): raise ValueError('duplicate tool')
        return self


class Answer(SafeContract):
    # Nested answers intentionally do not require the top-level version marker.
    schema_version: Literal[1] = 1
    value: Any = None
    status: Literal['known', 'unknown']
    source: Source
    confirmed: bool

    @model_validator(mode='after')
    def coherent(self):
        if self.status == 'unknown' and (self.value is not None or self.confirmed):
            raise ValueError('unknown answer has no confirmed value')
        if len(canonical(self.value)) > 128 * 1024: raise ValueError('answer too large')
        return self


REQUIRED = ('target_path', 'policy_path', 'binding_path', 'development', 'tool_binding', 'catalog')
OPTIONAL = ('binding_mode', 'repository', 'base_branch', 'state_dir', 'development_policy_path')


class QuestionnaireDraft(SafeContract):
    kind: Literal['questionnaire_draft'] = 'questionnaire_draft'
    answers: dict[str, Answer]

    @model_validator(mode='after')
    def known_fields(self):
        if not set(self.answers) <= set(REQUIRED + OPTIONAL): raise ValueError('unknown question')
        return self


def collect(draft):
    questions, values = [], {}
    fields = []
    for key in REQUIRED + OPTIONAL:
        answer = draft.answers.get(key)
        fields.append(dict(field=key,requirement='required' if key in REQUIRED else 'optional',
            status=answer.status if answer else 'unknown',source=answer.source if answer else None,
            confirmed=bool(answer and answer.confirmed)))
        if answer and answer.status == 'known' and answer.confirmed and answer.value is not None:
            if key == 'target_path' and not isinstance(answer.value,str):
                questions.append(dict(field=key,requirement='required',reason='ambiguous_target'))
            else: values[key] = answer.value
        elif key in REQUIRED:
            questions.append(dict(field=key, requirement='required',
                reason='confirm_local_fact' if answer and answer.source == 'local' else 'missing_decision'))
    return dict(schema_version=1, command='onboard', status='blocked' if questions else 'ready',
        checks=[], questions=questions, values=values, fields=fields, draft=draft.model_dump())


class GuidedRequest(SafeContract):
    kind: Literal['guided_request'] = 'guided_request'
    target_path: str
    policy_path: str
    binding_path: str
    binding_mode: Literal['existing', 'proposed'] = 'existing'
    repository: Repo | None = None
    base_branch: Branch | None = None
    state_dir: str | None = None
    development_policy_path: str | None = None
    development: ClientDevelopmentConfig
    tool_binding: ClientToolBinding
    catalog: RoleCatalog

    @model_validator(mode='after')
    def coherent(self):
        paths = [self.target_path, self.policy_path, self.binding_path]
        if self.state_dir: paths.append(self.state_dir)
        separate(paths)
        for path in paths: unmanaged_path(path)
        if self.development_policy_path:
            unmanaged_path(self.development_policy_path)
            separate([self.target_path, self.binding_path, self.development_policy_path])
        if self.binding_mode == 'proposed' and not self.state_dir: raise ValueError('state_dir required')
        if self.binding_mode == 'existing' and self.state_dir is not None: raise ValueError('binding already selects state')
        if self.development.client_id != self.tool_binding.client_id: raise ConfigError('client_mismatch')
        if set(self.development.roles) != {r.id for r in self.catalog.roles if r.activated}:
            raise ConfigError('guided_role_mismatch')
        return self


class CompositePreparationPlan(OnboardingPlan):
    kind: Literal['composite_preparation_plan'] = 'composite_preparation_plan'


class GuidedOnboardingPlan(SafeContract):
    kind: Literal['guided_onboarding_plan'] = 'guided_onboarding_plan'
    run_id: ID
    request: GuidedRequest
    provenance: QuestionnaireDraft
    target_identity: str
    init_v1: OnboardingPlan
    preparation: CompositePreparationPlan
    integration_edits: Annotated[list[IntegrationEdit], Field(max_length=16)]
    desktop_resource_sha256: SHA
    guided_resource_sha256: SHA
    development_policy_sha256: SHA | None
    blockers: list[str]
    plan_sha256: SHA

    @model_validator(mode='after')
    def integrity(self):
        if self.plan_sha256 != sha(canonical(self.model_dump(exclude={'plan_sha256'}))):
            raise ValueError('plan integrity')
        if len(canonical(self.model_dump())) > 1024 * 1024: raise ValueError('plan too large')
        return self


class StageRecord(Contract):
    name: Literal['preflight', 'collect', 'preview', 'prepare', 'integrate', 'certify']
    status: Literal['not_run', 'in_progress', 'completed', 'failed', 'blocked', 'recovered', 'conflict']
    error_code: str | None = None


class OnboardingRun(Contract):
    kind: Literal['onboarding_run'] = 'onboarding_run'
    client_id: ID
    checkout_id: ID
    run_id: ID
    plan_sha256: SHA
    target_identity: str
    stages: list[StageRecord]
    operations: list[OperationRecord]
    integration_plan_sha256: SHA | None = None


class CertificationInput(SafeContract):
    kind: Literal['onboarding_certification_input'] = 'onboarding_certification_input'
    certificate: DesktopCertificate
    snapshot: CandidateSnapshot
    acceptance: SupervisedAcceptance | None
    required_capabilities: list[str]
