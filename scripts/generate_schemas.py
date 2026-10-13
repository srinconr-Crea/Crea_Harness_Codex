"""Regenerar únicamente los schemas del producto desde sus contratos."""
import json
from pathlib import Path

from harness_core.contracts import Descriptor, Policy, Binding
from harness_core.onboarding_plan import OnboardingPlan, Journal
from harness_local.execution_state import LockOwner
from harness_core.quality import PracticePack, TestCase, TestCatalog, EvalCase, EvalCatalog, PracticeExtension
from harness_core.desktop import (ToolRequirement, RoleCatalog, RoleAssignment, DesktopIntegrationPlan,
                                  IntegrationJournal, DesktopCertificate)
from harness_core.supervised import CandidateSnapshot, SupervisedAcceptance
from harness_core.guided import (ClientDevelopmentConfig, ClientToolBinding, QuestionnaireDraft, GuidedRequest,
                                  CompositePreparationPlan, GuidedOnboardingPlan, OnboardingRun, CertificationInput)
from harness_core.hu import (HuRun,PlanRevision,ApprovalRecord,Candidate,Assignment,GateResult,Evidence,Handoff,
                             Start,PlanInput,Approval,Transition,WorktreeInput)

root = Path(__file__).resolve().parents[1] / 'schemas'
root.mkdir(exist_ok=True)
package_root = root.parent / 'src/harness_core/schemas'
package_root.mkdir(exist_ok=True)
for model in (Descriptor, Policy, Binding, OnboardingPlan, Journal, LockOwner,
              PracticePack, TestCase, TestCatalog, EvalCase, EvalCatalog, PracticeExtension,
              ToolRequirement, RoleCatalog, RoleAssignment, DesktopIntegrationPlan, IntegrationJournal, DesktopCertificate,
              CandidateSnapshot, SupervisedAcceptance, ClientDevelopmentConfig, ClientToolBinding, QuestionnaireDraft,
              GuidedRequest, CompositePreparationPlan, GuidedOnboardingPlan, OnboardingRun, CertificationInput,
              HuRun,PlanRevision,ApprovalRecord,Candidate,Assignment,GateResult,Evidence,Handoff,
              Start,PlanInput,Approval,Transition,WorktreeInput):
    name = model.__name__.lower() + '.schema.json'
    content = json.dumps(model.model_json_schema(), indent=2) + '\n'
    (root / name).write_text(content, encoding='utf-8')
    (package_root / name).write_text(content, encoding='utf-8')
