"""Supported manual import. Automatic Desktop execution is explicitly unavailable."""
from typing import Literal

from pydantic import Field

from harness_core.configuration import ConfigError
from harness_core.contracts import Contract
from harness_core.evaluation import EvalProfile, EvalRun, promotion_report, select_cases
from .observability_service import parse
from .quality_resources import load_quality


class EvalInput(Contract):
    milestone: int = Field(ge=1, le=8)
    purpose: Literal['development', 'promotion']
    profiles: list[EvalProfile] = Field(min_length=1, max_length=16)
    runs: list[EvalRun] = Field(max_length=10000)
    budget_runs: int = Field(ge=1, le=10000)
    execution_mode: Literal['manual', 'automatic']


def dispatch(action, value):
    if action not in ('validate', 'run', 'report'):
        raise ConfigError('invalid_eval_action')
    request = parse(EvalInput, value)
    if request.milestone > 7:
        raise ConfigError('milestone_not_available')
    bundle = load_quality()
    for profile in request.profiles:
        if (profile.dataset_sha256, profile.kit_sha256) != (bundle.dataset_sha256, bundle.manifest_sha256):
            raise ConfigError('eval_resource_version_mismatch')
    selected, _ = select_cases(bundle.evals, milestone=request.milestone, purpose=request.purpose)
    required = len(selected) * bundle.evals.default_repetitions * len(request.profiles)
    if required > request.budget_runs:
        raise ConfigError('eval_budget_exceeded')
    result = promotion_report(bundle.evals, request.profiles, request.runs,
                              milestone=request.milestone, purpose=request.purpose)
    result.update(action=action, required_runs=required, budget_runs=request.budget_runs,
        dataset_sha256=bundle.dataset_sha256, kit_sha256=bundle.manifest_sha256,
        imported_runs=[r.model_dump() for r in request.runs])
    if action == 'validate':
        result.update(status='valid', promotion_allowed=False)
        for item in result['profiles']:
            item['promotion_allowed'] = False
        return result, 0
    if request.execution_mode == 'automatic':
        result.update(status='blocked', promotion_allowed=False,
                      reason='supported_desktop_automation_unavailable')
        for item in result['profiles']:
            item['promotion_allowed'] = False
    return result, 0 if result['promotion_allowed'] else 1
