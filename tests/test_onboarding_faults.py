from pathlib import Path

import pytest

from harness_core.configuration import ConfigError
from test_onboarding_execution import setup, ready


@pytest.mark.parametrize('point', range(1, 43))
@pytest.mark.parametrize('after', [False, True])
def test_each_durable_boundary_preserves_uncertain_files(client, monkeypatch, point, after):
    from harness_local import application
    from harness_core.onboarding_plan import Journal, load_json
    path, plan = setup(client)
    original = application.persist
    count = 0
    triggered = False
    def interrupt(destination, journal):
        nonlocal count, triggered
        count += 1
        if count == point:
            triggered = True
            if after:
                original(destination, journal)
            raise ConfigError('injected_boundary')
        return original(destination, journal)
    monkeypatch.setattr(application, 'persist', interrupt)
    try:
        result, _ = application.apply(client['target'], client['policy'], path, probe_fn=ready)
    except ConfigError as error:
        assert error.code == 'injected_boundary'
    assert triggered, f'Boundary {point} not exercised; result: {result}'
    monkeypatch.setattr(application, 'persist', original)
    journals = list(Path(plan['binding']['state_dir']).glob('onboarding/*/journal.json'))
    if not journals:
        assert not (client['target'] / 'AGENTS.md').exists()
        return
    journal = load_json(journals[0], Journal)
    uncertain = [e for e in journal.operations if e.kind == 'file' and e.state == 'creating'
                 and (client['target'] / e.path if e.scope == 'target' else Path(e.path)).exists()]
    application.recover(client['target'], client['policy'], journal.run_id, plan_path=path, apply_changes=True)
    for e in uncertain:
        assert (client['target'] / e.path if e.scope == 'target' else Path(e.path)).exists()
    assert (client['target'] / '.harness/client.yaml').exists()


def test_runtime_command_guard_and_optional_tool_readiness(client, monkeypatch):
    from harness_local.application import apply
    from harness_local import diagnostics
    from harness_local.diagnostics import Check
    path, _ = setup(client)
    original = diagnostics.subprocess.Popen
    commands = []
    def guarded(argv, *args, **kwargs):
        commands.append(argv)
        name = Path(argv[0]).stem.lower()
        if name == 'git':
            assert any(a in argv for a in ('rev-parse', 'remote', 'status', 'config', 'symbolic-ref'))
        elif name in ('python', 'node', 'databricks'):
            assert '--version' in argv
        else:
            raise AssertionError(f'Unexpected runtime executable {name}')
        return original(argv, *args, **kwargs)
    monkeypatch.setattr(diagnostics.subprocess, 'Popen', guarded)
    def optional_absent(name):
        return Check(name, 'missing', 'tool_missing', 'fixture') if name == 'node' else ready(name)
    result, code = apply(client['target'], client['policy'], path, probe_fn=optional_absent)
    assert result['application_status'] == 'completed' and code == 1
    assert any(c['id'] == 'databricks_auth' and c['status'] == 'not_checked' for c in result['checks'])
    assert commands
