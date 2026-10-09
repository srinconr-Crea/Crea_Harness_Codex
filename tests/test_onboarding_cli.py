import json

from harness_local.cli import main
from test_onboarding_execution import setup


def test_cli_apply_recover_and_exclusive_modes(client, capsys):
    plan_path, plan = setup(client)
    args = ['--path', str(client['target']), '--policy', str(client['policy']), '--json']
    assert main(['init', '--dry-run', '--apply', *args]) == 2
    assert json.loads(capsys.readouterr().out)['status'] == 'invalid'
    code = main(['init', '--apply', '--plan', str(plan_path), *args])
    applied = json.loads(capsys.readouterr().out)
    assert code in (0, 1) and applied['application_status'] == 'completed'
    code = main(['recover', '--dry-run', '--plan', str(plan_path), '--run', applied['run_id'], *args])
    assert code == 0
    assert json.loads(capsys.readouterr().out)['recovery_status'] == 'preview'
    assert main(['recover', '--apply', '--binding', plan['binding_path'], '--run', applied['run_id'], *args]) == 0
    assert json.loads(capsys.readouterr().out)['recovery_status'] == 'recovered'


def test_cli_binding_proposal_and_human_hashes(client, capsys):
    plan_path, plan = setup(client)
    assert main(['init', '--dry-run', '--path', str(client['target']), '--policy', str(client['policy']),
                 '--binding-out', plan['binding_path'], '--checkout-id', 'new', '--state-dir', plan['binding']['state_dir'],
                 '--plan-out', str(plan_path.parent / 'second.json')]) in (0, 1)
    text = capsys.readouterr().out
    assert 'SHA256 plan:' in text and plan['plan_sha256'] in text
