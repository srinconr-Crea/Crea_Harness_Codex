import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from harness_core.configuration import ConfigError
from harness_core.onboarding_plan import canonical, sha
from test_onboarding_execution import setup, ready, snapshot


def test_global_state_and_binding_rejected(client):
    from harness_local.onboarding import preview
    for field in ('state_dir', 'binding_out'):
        kw = dict(binding_out=client['binding'].parent / 'new.json', checkout_id='new',
                  state_dir=client['binding'].parent / 'state/alpha/new')
        kw[field] = Path.home() / '.codex/alpha/new'
        with pytest.raises(ConfigError, match='managed_path'):
            preview(client['target'], client['policy'], **kw, probe_fn=ready)


def test_contract_limits_and_generated_schemas(client):
    from harness_core.onboarding_plan import OnboardingPlan, Journal, load_plan
    from harness_local.execution_state import LockOwner
    path, plan = setup(client)
    for mutation in ('duplicate', 'count', 'bytes', 'unknown', 'alias'):
        modified = json.loads(json.dumps(plan))
        if mutation == 'duplicate':
            modified['operations'].append(modified['operations'][0])
        elif mutation == 'count':
            modified['operations'] *= 7
        elif mutation == 'unknown':
            modified['kind'] = 'shell_script'
        elif mutation == 'alias':
            op = dict(modified['operations'][0])
            op['path'] = op['path'].upper()
            modified['operations'].append(op)
        else:
            op = modified['operations'][0]
            op['content'] = 'é' * 70000
            op['sha256'] = sha(op['content'].encode('utf-8'))
        modified.pop('plan_sha256')
        modified['plan_sha256'] = sha(canonical(modified))
        path.write_bytes(canonical(modified))
        with pytest.raises(ConfigError):
            load_plan(path)
    for model in (OnboardingPlan, Journal, LockOwner):
        assert json.loads(Path('schemas', model.__name__.lower() + '.schema.json').read_text()) == model.model_json_schema()


def test_orphan_lock_requires_explicit_recovery_and_pid_reuse(client):
    from harness_core.onboarding_plan import load_plan
    from harness_local.execution_state import CheckoutLock, ensure_state, process_identity
    path, _ = setup(client)
    state = ensure_state(load_plan(path).binding)
    lock = state / 'onboarding.lock'
    # A real process that has exited, with a captured birth time.
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(2)'])
    started = process_identity(child.pid)
    child.wait(timeout=5)
    lock.write_text(json.dumps(dict(schema_version=1, pid=child.pid, started=started, run_id='old')))
    with pytest.raises(ConfigError, match='onboarding_locked'):
        with CheckoutLock(state, 'new'):
            pass
    with CheckoutLock(state, 'new', recover=True):
        assert lock.exists()
    assert not lock.exists()
    # Same PID, different birth identity is an old owner, not the live process.
    lock.write_text(json.dumps(dict(schema_version=1, pid=os.getpid(), started='1', run_id='old')))
    with CheckoutLock(state, 'new', recover=True):
        pass
    lock.write_text('{"pid":1,"pid":2}')
    with pytest.raises(ConfigError):
        with CheckoutLock(state, 'new', recover=True):
            pass
    assert lock.exists()


def test_real_second_process_lock_rejects_apply(client):
    from harness_local.application import apply
    from harness_local.execution_state import CheckoutLock, ensure_state
    from harness_core.onboarding_plan import load_plan
    path, _ = setup(client)
    state = ensure_state(load_plan(path).binding)
    signal = path.parent / 'locked'
    script = path.parent / 'holder.py'
    script.write_text('import sys,time\nfrom pathlib import Path\nfrom harness_local.execution_state import CheckoutLock\n'
        'with CheckoutLock(sys.argv[1], "other"):\n Path(sys.argv[2]).touch()\n time.sleep(10)\n')
    env = dict(os.environ, PYTHONPATH=str(Path('src').resolve()))
    child = subprocess.Popen([sys.executable, str(script), str(state), str(signal)], env=env)
    try:
        import time
        deadline = time.monotonic() + 5
        while not signal.exists() and time.monotonic() < deadline:
            time.sleep(.05)
        assert signal.exists()
        before = snapshot(client['target'])
        with pytest.raises(ConfigError, match='onboarding_locked'):
            apply(client['target'], client['policy'], path, probe_fn=ready)
        assert snapshot(client['target']) == before
    finally:
        child.terminate()
        child.wait(timeout=5)


def test_unprepared_beta_existing_code_specs_and_prepared_conflict(client):
    from harness_local.application import apply
    from harness_local.onboarding import preview
    from harness_core.onboarding_plan import load_plan
    path, _ = setup(client)
    target = client['target']
    data = json.loads(client['policy'].read_text())
    data.update(client_id='beta', repository='demo/beta')
    client['policy'].write_text(json.dumps(data))
    subprocess.run(['git', '-C', str(target), 'remote', 'set-url', 'origin', 'https://github.com/demo/beta.git'], check=True)
    (target / '.harness/client.yaml').unlink()
    (target / 'code.py').write_text('raise RuntimeError("NEVER_EXECUTE")')
    (target / 'openspec/specs/business').mkdir(parents=True)
    (target / 'openspec/specs/business/spec.md').write_text('Client spec')
    (target / 'openspec/changes/custom').mkdir(parents=True)
    (target / 'openspec/changes/custom/tasks.md').write_text('Client change')
    before = snapshot(target)
    beta = path.parent / 'beta-plan.json'
    result, _ = preview(target, client['policy'], repo='demo/beta', base_branch='develop', probe_fn=ready,
        binding_out=path.parent / 'beta-binding.json', checkout_id='new', state_dir=path.parent / 'state/beta/new', plan_out=beta)
    assert snapshot(target) == before
    applied, _ = apply(target, client['policy'], beta, probe_fn=ready)
    assert applied['application_status'] == 'completed'
    after = snapshot(target)
    assert all(after[p] == value for p, value in before.items())
    binding = load_plan(beta).binding_path
    result, _ = preview(target, client['policy'], binding, probe_fn=ready)
    assert result['applicable'] and result['plan']['operations'] == []
    (target / 'AGENTS.md').write_text('Custom instructions')
    result, _ = preview(target, client['policy'], binding, probe_fn=ready)
    assert not result['applicable']


def test_nonempty_directory_and_changed_policy_preserved(client):
    from harness_local.application import apply, recover
    path, plan = setup(client)
    result, _ = apply(client['target'], client['policy'], path, probe_fn=ready)
    keep = client['target'] / '.agents/keep.txt'
    keep.write_text('developer')
    recovered, code = recover(client['target'], client['policy'], result['run_id'], plan_path=path, apply_changes=True)
    assert code == 1 and recovered['recovery_status'] == 'recovery_conflict' and keep.read_text() == 'developer'
    client['policy'].write_text(client['policy'].read_text() + '\n')
    before = snapshot(client['target'].parent)
    with pytest.raises(ConfigError, match='stale_plan'):
        recover(client['target'], client['policy'], result['run_id'], plan_path=path, apply_changes=True)
    assert snapshot(client['target'].parent) == before


@pytest.mark.parametrize('path,pattern,want', [
    ('AGENTS.md','**/AGENTS.md',True),
    ('a/b/AGENTS.md','**/AGENTS.md',True),
    ('a/x/b','a/**/b',True),
    ('a/b','a/**/b',True),
    ('a/b/c','a/*/c',True),
    ('a/x/b/c','a/*/c',False),
    ('PRIVATE/a','private/',True),
    ('a/x/b','a/?/b',True),
    ('a/xy/b','a/?/b',False),
])
def test_policy_globs_zero_components_and_case(path, pattern, want):
    from harness_core.onboarding_plan import denied
    assert denied(path, [pattern]) is want


def test_relative_openspec_root_and_existing_binding_preconditions(client):
    from harness_local.onboarding import preview
    from harness_local.application import apply
    from harness_core.configuration import digest
    descriptor = client['target'] / '.harness/client.yaml'
    data = json.loads(descriptor.read_text())
    data['openspec_root'] = 'planning/openspec'
    descriptor.write_text(json.dumps(data))
    policy = json.loads(client['policy'].read_text())
    policy['read_only_paths'] = []
    client['policy'].write_text(json.dumps(policy))
    binding = json.loads(client['binding'].read_text())
    binding['policy_sha256'] = digest(client['policy'])
    client['binding'].write_text(json.dumps(binding))
    path = client['binding'].parent / 'existing-plan.json'
    result, _ = preview(client['target'], client['policy'], client['binding'], probe_fn=ready, plan_out=path)
    assert any(o['path'] == 'planning/openspec/config.yaml' for o in result['plan']['operations'])
    client['binding'].write_text(client['binding'].read_text() + '\n')
    before = snapshot(client['target'])
    with pytest.raises(ConfigError, match='stale_plan'):
        apply(client['target'], client['policy'], path, probe_fn=ready)
    assert snapshot(client['target']) == before
    client['binding'].write_text(json.dumps(binding))
    applied, _ = apply(client['target'], client['policy'], path, probe_fn=ready)
    assert applied['application_status'] == 'completed'
    assert (client['target'] / 'planning/openspec/config.yaml').exists()


def test_export_linked_parent_rejected(client):
    from harness_local.onboarding import preview
    path, plan = setup(client)
    outside = path.parent / 'outside'
    outside.mkdir()
    link = path.parent / 'linked'
    command = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(outside)], capture_output=True)
    assert command.returncode == 0
    with pytest.raises(ConfigError, match='linked_path'):
        preview(client['target'], client['policy'], probe_fn=ready,
                binding_out=plan['binding_path'], checkout_id='new', state_dir=plan['binding']['state_dir'],
                plan_out=link / 'export.json')
    assert not (outside / 'export.json').exists()
