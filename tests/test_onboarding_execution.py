import hashlib
import json
from pathlib import Path

import pytest

from harness_core.configuration import ConfigError
from harness_local.diagnostics import Check
from harness_local.onboarding import preview


def ready(name):
    return Check(name, 'ready', 'compatible', 'fixture')


def setup(client):
    data = json.loads(client['policy'].read_text())
    data['read_only_paths'] = []
    client['policy'].write_text(json.dumps(data))
    path = client['binding'].parent / 'plan.json'
    kw = dict(binding_out=client['binding'].parent / 'new.json', checkout_id='new',
              state_dir=client['binding'].parent / 'state/alpha/new')
    result, _ = preview(client['target'], client['policy'], probe_fn=ready, plan_out=path, **kw)
    return path, result['plan']


def snapshot(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def test_apply_repeat_doctor_and_recovery_preserves_existing(client):
    from harness_local.application import apply, recover
    plan_path, plan = setup(client)
    descriptor = (client['target'] / '.harness/client.yaml').read_bytes()
    result, code = apply(client['target'], client['policy'], plan_path, probe_fn=ready)
    assert result['application_status'] == 'completed' and code == 0
    assert any(c['code'] == 'desktop_not_verified' for c in result['checks'])
    assert Path(plan['binding_path']).exists()
    before = snapshot(client['target'].parent)
    repeated, _ = apply(client['target'], client['policy'], plan_path, probe_fn=ready)
    assert repeated['run_id'] == result['run_id'] and repeated['idempotent']
    assert snapshot(client['target'].parent) == before
    preview_result, _ = recover(client['target'], client['policy'], result['run_id'], plan_path=plan_path)
    assert preview_result['recovery_status'] == 'preview'
    assert snapshot(client['target'].parent) == before
    recovered, code = recover(client['target'], client['policy'], result['run_id'],
                              binding_path=plan['binding_path'], apply_changes=True)
    assert code == 0 and recovered['recovery_status'] == 'recovered'
    assert (client['target'] / '.harness/client.yaml').read_bytes() == descriptor
    assert not (client['target'] / 'AGENTS.md').exists()
    assert not Path(plan['binding_path']).exists()
    assert not (client['target'] / '.agents').exists()


@pytest.mark.parametrize('mutation', ['policy', 'origin', 'absence', 'payload', 'redirect'])
def test_preflight_rejection_no_client_writes(client, mutation):
    from harness_local.application import apply
    from harness_core.onboarding_plan import canonical, sha
    plan_path, plan = setup(client)
    if mutation == 'policy':
        client['policy'].write_text(client['policy'].read_text() + '\n')
    elif mutation == 'origin':
        import subprocess
        subprocess.run(['git', '-C', str(client['target']), 'remote', 'set-url', 'origin', 'https://github.com/demo/beta.git'], check=True)
    elif mutation == 'absence':
        (client['target'] / 'AGENTS.md').write_text('custom')
    elif mutation == 'redirect':
        plan['target_path'] = str(client['target'].parent / 'other')
    else:
        plan['operations'][0]['content'] = 'arbitrary reviewed?'
        plan['operations'][0]['sha256'] = sha(b'arbitrary reviewed?')
    if mutation in ('payload', 'redirect'):
        plan.pop('plan_sha256')
        plan['plan_sha256'] = sha(canonical(plan))
        plan_path.write_bytes(canonical(plan))
    before = snapshot(client['target'].parent)
    with pytest.raises(ConfigError):
        apply(client['target'], client['policy'], plan_path, probe_fn=ready)
    assert snapshot(client['target'].parent) == before


def test_failure_recovery_before_binding_and_modified_owned_file(client, monkeypatch):
    from harness_local.application import apply, recover
    from harness_local.windows_fs import Handle
    plan_path, plan = setup(client)
    original = Handle.write
    count = 0
    def fail(self, data):
        nonlocal count
        if data == b'write trigger':
            raise AssertionError()
        # Fail on AGENTS, after some Skills have their durable completion.
        if data.startswith(b'# Instrucciones'):
            raise ConfigError('injected_failure')
        return original(self, data)
    # Inject after a durable created operation instead of depending on prose.
    from harness_local import application
    persist = application.persist
    def crash(path, journal):
        nonlocal count
        persist(path, journal)
        if any(o.state == 'created' and o.kind == 'file' for o in journal.operations):
            count += 1
            if count == 1:
                raise ConfigError('injected_failure')
    monkeypatch.setattr(application, 'persist', crash)
    failed, code = apply(client['target'], client['policy'], plan_path, probe_fn=ready)
    assert code == 1 and failed['application_status'] == 'failed'
    assert not Path(plan['binding_path']).exists()
    monkeypatch.setattr(application, 'persist', persist)
    owned = next(o for o in failed['operations'] if o['kind'] == 'file' and o['state'] == 'created')
    path = client['target'] / owned['path']
    path.write_text('developer edit')
    result, code = recover(client['target'], client['policy'], failed['run_id'], plan_path=plan_path, apply_changes=True)
    assert result['recovery_status'] == 'recovery_conflict' and code == 1
    assert path.read_text() == 'developer edit'


def test_ambiguous_partial_and_foreign_journal(client, monkeypatch):
    from harness_local.application import apply, recover
    from harness_local.windows_fs import Handle
    plan_path, plan = setup(client)
    original = Handle.write
    skill = plan['operations'][0]['content'].encode('utf-8')
    def partial(self, data):
        if data == skill:
            original(self, b'partial')
            raise ConfigError('interrupted')
        original(self, data)
    monkeypatch.setattr(Handle, 'write', partial)
    failed, _ = apply(client['target'], client['policy'], plan_path, probe_fn=ready)
    ambiguous = client['target'] / plan['operations'][0]['path']
    assert ambiguous.read_bytes() == b'partial'
    monkeypatch.setattr(Handle, 'write', original)
    before = snapshot(client['target'].parent)
    result, code = recover(client['target'], client['policy'], failed['run_id'], plan_path=plan_path)
    assert code == 1 and any(o['state'] == 'conflict' for o in result['operations'])
    assert snapshot(client['target'].parent) == before
    journal = Path(plan['binding']['state_dir']) / 'onboarding' / failed['run_id'] / 'journal.json'
    data = json.loads(journal.read_text())
    data['client_id'] = 'beta'
    journal.write_text(json.dumps(data))
    with pytest.raises(ConfigError):
        recover(client['target'], client['policy'], failed['run_id'], plan_path=plan_path, apply_changes=True)
    assert ambiguous.exists()


def test_checkout_lock_process_identity(client):
    from harness_local.execution_state import CheckoutLock, process_identity
    from harness_core.onboarding_plan import load_plan
    path, _ = setup(client)
    plan = load_plan(path)
    from harness_local.execution_state import ensure_state
    state = ensure_state(plan.binding)
    first = CheckoutLock(state, 'a')
    with first:
        with pytest.raises(ConfigError, match='onboarding_locked'):
            with CheckoutLock(state, 'b'):
                pass
        assert process_identity(first.pid) == first.started
        with pytest.raises(ConfigError, match='onboarding_locked'):
            with CheckoutLock(state, 'b', recover=True):
                pass


def test_apply_after_full_recovery_reuses_deterministic_plan(client):
    from harness_local.application import apply, recover
    path, _ = setup(client)
    first, _ = apply(client['target'], client['policy'], path, probe_fn=ready)
    recovered, code = recover(client['target'], client['policy'], first['run_id'], plan_path=path, apply_changes=True)
    assert code == 0
    # A new export has exactly the same hash after all creations are removed.
    path.unlink()
    path, _ = setup(client)
    second, _ = apply(client['target'], client['policy'], path, probe_fn=ready)
    assert second['application_status'] == 'completed' and second['run_id'] != first['run_id']


def test_target_cannot_be_replaced_between_preflight_and_journal(client, monkeypatch):
    from harness_local import application
    path, _ = setup(client)
    original = application.persist
    attempted = False
    def replace(destination, journal):
        nonlocal attempted
        if not attempted:
            attempted = True
            with pytest.raises(OSError):
                client['target'].rename(client['target'].parent / 'original')
        original(destination, journal)
    monkeypatch.setattr(application, 'persist', replace)
    result, _ = application.apply(client['target'], client['policy'], path, probe_fn=ready)
    assert attempted and result['application_status'] == 'completed'
