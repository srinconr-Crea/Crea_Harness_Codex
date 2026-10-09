"""Exercise the installed wheel, using only disposable synthetic checkouts."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid
from zipfile import ZipFile

root = Path(__file__).resolve().parents[1]
interpreter = root / '.smoke-venv/Scripts/python.exe'
entry = root / '.smoke-venv/Scripts/harness.exe'
fixture = root / '.test-data' / ('wheel-onboarding-' + uuid.uuid4().hex)
fixture.mkdir(parents=True)
env = dict(os.environ, OPENSPEC_TELEMETRY='0', OPENSPEC_NO_UPDATE_CHECK='1')
env.pop('PYTHONPATH', None)
checks = []


def invoke(arguments, accepted=(0,)):
    result = subprocess.run([str(a) for a in arguments], cwd=fixture, env=env,
                            capture_output=True, encoding='utf-8', timeout=60)
    assert result.returncode in accepted, (arguments, result.returncode, result.stdout, result.stderr)
    checks.append(dict(command=[str(a) for a in arguments], exit_code=result.returncode))
    return result.stdout


def snapshot(path):
    return {p.relative_to(path).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in path.rglob('*') if p.is_file()}


invoke([interpreter, '-I', '-c', "from importlib.resources import files; import json,harness_local; from harness_local.resources import kit; assert 'site-packages' in harness_local.__file__; assert len(kit()[0])==8; from harness_core.onboarding_plan import OnboardingPlan,Journal; assert json.loads(files('harness_core').joinpath('schemas/onboardingplan.schema.json').read_text())==OnboardingPlan.model_json_schema(); assert json.loads(files('harness_core').joinpath('schemas/journal.schema.json').read_text())==Journal.model_json_schema()"])
clients = []
for client in ('alpha', 'beta'):
    directory = fixture / client
    directory.mkdir()
    target = directory / 'target'
    invoke(['git', 'init', '--initial-branch=develop', target])
    invoke(['git', '-C', target, 'remote', 'add', 'origin', f'https://github.com/demo/{client}.git'])
    policy = directory / 'policy.json'
    policy.write_text(json.dumps(dict(schema_version=1, policy_id='pilot', client_id=client,
        repository=f'demo/{client}', base_branch='develop', branch_prefix='feature/',
        read_only_paths=[], denied_paths=['private/'], max_files=40, max_bytes=2000000)))
    binding = directory / 'binding.json'
    state = directory / 'state' / client / 'checkout'
    before = snapshot(target)
    plan = directory / 'plan.json'
    exported = json.loads(invoke([entry, 'init', '--dry-run', '--path', target, '--policy', policy,
        '--binding-out', binding, '--checkout-id', 'checkout', '--state-dir', state,
        '--repo', f'demo/{client}', '--base-branch', 'develop', '--plan-out', plan, '--json'], (0, 1)))
    assert exported['applicable'] and snapshot(target) == before and not binding.exists() and not state.exists()
    applied = json.loads(invoke([entry, 'init', '--apply', '--path', target, '--policy', policy, '--plan', plan, '--json'], (0, 1)))
    assert applied['application_status'] == 'completed'
    assert any(c['id'] == 'databricks_auth' and c['status'] == 'not_checked' for c in applied['checks'])
    after = snapshot(directory)
    repeated = json.loads(invoke([entry, 'init', '--apply', '--path', target, '--policy', policy, '--plan', plan, '--json'], (0, 1)))
    assert repeated['idempotent'] and repeated['run_id'] == applied['run_id'] and snapshot(directory) == after
    reviewed = json.loads(invoke([entry, 'recover', '--dry-run', '--path', target, '--policy', policy,
        '--plan', plan, '--run', applied['run_id'], '--json']))
    assert reviewed['recovery_status'] == 'preview' and snapshot(directory) == after
    recovered = json.loads(invoke([entry, 'recover', '--apply', '--path', target, '--policy', policy,
        '--binding', binding, '--run', applied['run_id'], '--json']))
    assert recovered['recovery_status'] == 'recovered' and snapshot(target) == before
    clients.append(dict(client=client, plan_sha256=exported['plan']['plan_sha256'],
                        application_status=applied['application_status'], recovery_status=recovered['recovery_status']))
wheel = root / 'dist/crea_local_harness-0.1.0-py3-none-any.whl'
with ZipFile(wheel) as archive:
    names = archive.namelist()
    assert len([name for name in names if 'openspec_kit/' in name and name.endswith('SKILL.md')]) == 7
    assert 'harness_core/schemas/onboardingplan.schema.json' in names
    assert {name for name in names if '/fixtures/' in name} == {
        'harness_local/quality_kit/fixtures/synthetic-sales.json'}
result = dict(wheel=wheel.name, sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),
              clients=clients, checks=checks, wheel_files=names)
(root / 'docs/evidence/onboarding-wheel-smoke.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(f'{len(checks)} installed-wheel checks passed; alpha and beta isolated')
