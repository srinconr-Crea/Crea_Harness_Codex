"""Regenerar únicamente los schemas del producto desde sus contratos."""
import json
from pathlib import Path

from harness_core.contracts import Descriptor, Policy, Binding
from harness_core.onboarding_plan import OnboardingPlan, Journal
from harness_local.execution_state import LockOwner

root = Path(__file__).resolve().parents[1] / 'schemas'
root.mkdir(exist_ok=True)
package_root = root.parent / 'src/harness_core/schemas'
package_root.mkdir(exist_ok=True)
for model in (Descriptor, Policy, Binding, OnboardingPlan, Journal, LockOwner):
    name = model.__name__.lower() + '.schema.json'
    content = json.dumps(model.model_json_schema(), indent=2) + '\n'
    (root / name).write_text(content, encoding='utf-8')
    (package_root / name).write_text(content, encoding='utf-8')
