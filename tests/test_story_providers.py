import pytest

from harness_core.configuration import ConfigError
from test_story_contracts import binding


def test_fixture_revision_and_injection():
    from harness_local.story_providers import FixtureStoryProvider
    provider = FixtureStoryProvider()
    one = provider.read_story(binding(), '17')
    provider.revision = 2
    two = provider.read_story(binding(), '17')
    assert one.snapshot_sha256 != two.snapshot_sha256
    assert two.repository == 'demo/alpha' and two.trust == 'external_data'


def test_github_read_uses_selected_identity_without_authentication_or_writes():
    from harness_local.story_providers import GitHubProvider
    calls = []
    def executor(operation, payload):
        calls.append(operation)
        if operation == 'repository': return {'full_name': 'demo/alpha'}
        return dict(number=17, updated_at='2026-10-13T00:00:00Z', title='Sumar', body='Suma decimal',
                    html_url='https://github.com/demo/alpha/issues/17')
    p = GitHubProvider(executor=executor)
    story = p.read_story(binding(), '17')
    assert story.source_id == '17' and story.criteria == ['Suma decimal']
    assert calls == ['repository', 'read_story']


@pytest.mark.parametrize('failure', ['credentials', 'wrong_repo', 'missing_capability', 'wrong_issue'])
def test_read_failures_do_not_write(failure):
    from harness_local.story_providers import GitHubProvider
    calls = []
    def executor(operation, payload):
        calls.append(operation)
        if failure == 'credentials': raise ConfigError('provider_unavailable')
        if operation == 'repository': return {'full_name': 'other/repo' if failure == 'wrong_repo' else 'demo/alpha'}
        return dict(number=18, updated_at='r', title='x', body='x', html_url='https://github.com/demo/alpha/issues/18')
    b = binding(); raw = b.model_dump()
    if failure == 'missing_capability': raw['capabilities'] = ['push']
    from harness_core.story import ProviderBinding
    with pytest.raises(ConfigError): GitHubProvider(executor=executor).read_story(ProviderBinding.model_validate(raw), '17')
    assert not set(calls) & {'push', 'create_pr', 'write_story'}


def test_mcp_requires_selected_supported_executor():
    from harness_local.story_providers import select_provider
    raw = binding().model_dump(); raw['transport'] = 'mcp'
    from harness_core.story import ProviderBinding
    with pytest.raises(ConfigError, match='provider_mcp_unavailable'):
        select_provider(ProviderBinding.model_validate(raw))


def test_cli_missing_tool_is_blocked_without_login(monkeypatch):
    from harness_local.story_providers import GitHubProvider
    monkeypatch.setattr('shutil.which', lambda _: None)
    with pytest.raises(ConfigError, match='provider_tool_missing'):
        GitHubProvider().read_story(binding(), '17')


def test_cli_push_rejects_git_url_rewrite_before_network(scratch, monkeypatch):
    import subprocess
    from harness_local.story_providers import GitHubProvider
    from test_publication import make_intent
    target=scratch/'repo'; target.mkdir()
    subprocess.run(['git','init',str(target)],check=True,capture_output=True)
    subprocess.run(['git','-C',str(target),'config','url.https://github.com/evil/repo.git.pushInsteadOf',
                    'https://github.com/demo/alpha.git'],check=True,capture_output=True)
    # Network entry must remain unreachable: only the read-only config probe is allowed.
    from harness_local import story_providers as module
    original=module.run_bounded
    def guarded(argv, **kwargs):
        if 'push' in argv: pytest.fail('unverified destination reached push')
        return original(argv,**kwargs)
    monkeypatch.setattr(module,'run_bounded',guarded)
    with pytest.raises(ConfigError,match='provider_destination_rewrite'):
        GitHubProvider(target=target).push(binding(),make_intent())


def test_mcp_push_requires_atomic_absent_branch_contract():
    from harness_local.story_providers import GitHubProvider
    from test_publication import make_intent
    i=make_intent()
    def executor(operation,payload):
        assert payload['expected_old_oid'] is None and payload['creation_only'] is True
        return dict(created=True,previous_oid=None,branch=i.head_branch,head=i.head_oid)
    GitHubProvider(executor=executor).push(binding(),i)


@pytest.mark.parametrize('kind', ['fixture', 'github'])
def test_invalid_story_id_is_public_input_error(kind):
    from harness_local.story_providers import FixtureStoryProvider,GitHubProvider
    provider=FixtureStoryProvider() if kind=='fixture' else GitHubProvider()
    with pytest.raises(ConfigError,match='invalid_story_id'):
        provider.read_story(binding(),'1'*5000)
