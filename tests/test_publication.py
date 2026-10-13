import json
from pathlib import Path

import pytest

from harness_core.configuration import ConfigError
from test_story_contracts import binding


def make_intent(**updates):
    from harness_core.story import intent, snapshot
    value = dict(intent_id='publish1', client_id='alpha', checkout_id='checkout', hu_id='HU1', attempt=1,
        provider='github', repository='demo/alpha', base_branch='develop', head_branch='feature/hu1',
        base_oid='a'*40, head_oid='b'*40, candidate_sha256='c'*64, context_sha256='d'*64,
        plan_sha256='e'*64, story=snapshot('demo/alpha', '17', 'rev1', 'Sumar', ['decimal'], []),
        title='Sumar por cliente', body='Implementa la HU17. Evidencia: T20.', evidence_refs=['T20'])
    value.update(updates)
    return intent(**value)


def authorization(value, **updates):
    from harness_core.story import PublicationAuthorization
    raw = dict(schema_version=1, actor='operator', confirmed=True, intent_sha256=value.intent_sha256,
        actions=['push', 'create_pr']); raw.update(updates)
    return PublicationAuthorization.model_validate(raw)


class Remote:
    """An external GitHub service double: mutations survive lost responses."""
    simulated = True
    def __init__(self):
        self.refs = {'develop': 'a'*40}; self.pulls = []; self.writes = []; self.loss = None
    def preflight(self, b): pass
    def read_story(self, b, source_id): return make_intent().story
    def branch(self, b, branch): return self.refs.get(branch)
    def prs(self, b, i): return self.pulls[:]
    def push(self, b, i):
        self.refs[i.head_branch] = i.head_oid; self.writes.append('push')
        if self.loss == 'push': self.loss = None; raise ConfigError('publication_outcome_unknown')
    def create_pr(self, b, i):
        from harness_local.story_providers import marker
        p = dict(number=17, html_url='https://github.com/demo/alpha/pull/17', draft=True, state='open',
            body=i.body+'\n'+marker(i), head=dict(ref=i.head_branch, sha=i.head_oid, repo=dict(full_name=i.repository)),
            base=dict(ref=i.base_branch, sha=i.base_oid, repo=dict(full_name=i.repository)))
        self.pulls.append(p); self.writes.append('create_pr')
        if self.loss == 'pr': self.loss = None; raise ConfigError('publication_outcome_unknown')
        return p


@pytest.fixture
def publisher(scratch):
    from harness_local.publication import PublicationService
    remote = Remote()
    # The real candidate verifier is tested separately against prepared HU/Git.
    state = scratch / 'state'; state.mkdir()
    service = PublicationService(binding(), remote, state, candidate_check=lambda i: None,
        evaluation_check=lambda e: None)
    return service, remote, state


def test_preview_does_not_create_state_or_call_provider(scratch):
    from harness_local.publication import preview
    i = make_intent()
    before = list(scratch.rglob('*'))
    result = preview(i, None, None)
    assert result['title'] == 'Sumar por cliente' and result['draft']
    assert not result['publication_allowed'] and result['status'] == 'partial'
    assert result['candidate_sha256'] == 'c'*64 and result['body'].endswith('-->')
    assert list(scratch.rglob('*')) == before


@pytest.mark.parametrize('updates', [dict(confirmed=False), dict(actions=['create_pr']), dict(intent_sha256='f'*64)])
def test_no_publication_permission_preserves_preview_and_remote(publisher, updates):
    service, remote, _ = publisher; i = make_intent()
    result = service.publish(i, authorization(i, **updates), None)
    assert result['status'] == 'blocked' and remote.writes == []


@pytest.mark.parametrize('reason', ['eval_not_run', 'eval_blocked', 'candidate_changed', 'context_changed', 'independent_review_required'])
def test_gate_failure_blocks_even_with_explicit_authorization(publisher, reason):
    service, remote, state = publisher; i = make_intent()
    service.candidate_check = lambda i: reason
    result = service.publish(i, authorization(i), None)
    assert result['reason'] == reason and not remote.writes
    assert not list(state.glob('*.sqlite3'))


def test_authorized_draft_and_repeat_never_duplicates(publisher):
    service, remote, _ = publisher; i = make_intent()
    one = service.publish(i, authorization(i), None)
    two = service.publish(i, authorization(i), None)
    assert one['status'] == two['status'] == 'published'
    assert two['receipt']['pr_url'] == 'https://github.com/demo/alpha/pull/17'
    assert remote.writes == ['push', 'create_pr']
    assert two['attachment_status'] == 'unavailable' and not two['certified']


@pytest.mark.parametrize('loss', ['push', 'pr'])
def test_lost_response_reconciles_durable_intent(publisher, loss):
    from harness_local.publication import PublicationService
    service, remote, state = publisher; i = make_intent(); remote.loss = loss
    first = service.publish(i, authorization(i), None)
    assert first['status'] == 'unknown'
    resumed = PublicationService(binding(), remote, state, candidate_check=lambda i: None, evaluation_check=lambda e: None)
    result = resumed.publish(i, authorization(i), None)
    assert result['status'] == 'published' and remote.writes == ['push', 'create_pr']


def test_foreign_branch_never_overwritten(publisher):
    service, remote, _ = publisher; i = make_intent()
    remote.refs[i.head_branch] = i.head_oid
    result = service.publish(i, authorization(i), None)
    assert result['reason'] == 'foreign_branch' and not remote.writes


@pytest.mark.parametrize('kind', ['base', 'story', 'repo', 'head', 'draft', 'marker'])
def test_existing_pr_mismatch_blocks(publisher, kind):
    service, remote, _ = publisher; i = make_intent()
    remote.refs[i.head_branch] = i.head_oid
    p = remote.create_pr(binding(), i); remote.writes.clear()
    if kind == 'base': remote.refs['develop'] = 'f'*40
    if kind == 'story': remote.read_story = lambda b, s: make_intent().story.model_copy(update={'revision': 'rev2'})
    if kind == 'repo': p['head']['repo']['full_name'] = 'evil/repo'
    if kind == 'head': p['head']['sha'] = 'f'*40
    if kind == 'draft': p['draft'] = False
    if kind == 'marker': p['body'] = 'foreign'
    result = service.publish(i, authorization(i), None)
    assert result['status'] == 'blocked' and not remote.writes


def test_existing_matching_pr_attaches_after_revalidation(publisher):
    service, remote, _ = publisher; i = make_intent(); urls = []
    remote.refs[i.head_branch] = i.head_oid; remote.create_pr(binding(), i); remote.writes.clear()
    def attach(url): urls.append(url); return True
    service.attach = attach
    result = service.publish(i, authorization(i), None)
    assert urls == ['https://github.com/demo/alpha/pull/17']
    assert result['receipt']['attached'] and remote.writes == []
    service.publish(i, authorization(i), None)
    assert urls == ['https://github.com/demo/alpha/pull/17']


def test_attach_error_result_is_not_recorded_as_attached(publisher):
    service, remote, _ = publisher; i = make_intent()
    service.attach = lambda url: {'isError': True}
    result = service.publish(i, authorization(i), None)
    assert result['attachment_status'] == 'failed' and not result['receipt']['attached']


def test_actual_pending_evaluations_block_publication_before_provider(publisher):
    from harness_local.publication import evaluation_gate
    from test_story_cli import pending
    service, remote, state = publisher; i = make_intent()
    service.evaluation_check = evaluation_gate
    result = service.publish(i, authorization(i), pending())
    assert result['reason'] == 'required_evaluations_blocked' and not remote.writes
    assert not list(state.iterdir())


def test_duplicate_existing_pr_is_blocked(publisher):
    service, remote, _ = publisher; i = make_intent()
    remote.refs[i.head_branch] = i.head_oid
    remote.create_pr(binding(), i); remote.create_pr(binding(), i); remote.writes.clear()
    result = service.publish(i, authorization(i), None)
    assert result['reason'] == 'duplicate_remote_pr' and not remote.writes


def test_second_intent_cannot_replace_branch_owner(publisher):
    service, remote, _ = publisher; i = make_intent()
    service.publish(i, authorization(i), None)
    other = make_intent(intent_id='publish2', title='otro')
    result = service.publish(other, authorization(other), None)
    assert result['reason'] == 'foreign_branch' and remote.writes == ['push', 'create_pr']


def test_preview_linked_destination_rejected(scratch):
    import os
    from harness_local.publication import preview
    target = scratch/'target'; target.mkdir()
    saved = scratch/'saved.json'; saved.write_text('preserve')
    out = scratch/'linked.json'; os.link(saved, out)
    with pytest.raises(ConfigError): preview(make_intent(), None, None, export=out, target=target)
    assert saved.read_text() == 'preserve'


def test_same_intent_id_with_different_candidate_is_conflict(publisher):
    service, remote, _ = publisher; i = make_intent()
    service.publish(i, authorization(i), None)
    other = make_intent(title='Otro resultado')
    result = service.publish(other, authorization(other), None)
    assert result['reason'] == 'publication_intent_conflict'
    assert remote.writes == ['push', 'create_pr']


def test_export_existing_destination_is_exclusive(scratch):
    from harness_local.publication import preview
    target = scratch / 'target'; target.mkdir(); out = scratch / 'plan.json'
    out.write_text('preserve')
    with pytest.raises(ConfigError): preview(make_intent(), None, None, export=out, target=target)
    assert out.read_text() == 'preserve'


def test_preview_export_inside_target_rejected(scratch):
    from harness_local.publication import preview
    target = scratch / 'target'; target.mkdir()
    with pytest.raises(ConfigError): preview(make_intent(), None, None, export=target/'plan.json', target=target)
    assert not (target/'plan.json').exists()


def test_changed_gate_before_create_pr_leaves_no_pr(publisher):
    service, remote, _ = publisher; i = make_intent()
    calls = []
    def gate(i):
        calls.append(1)
        return 'candidate_changed' if len(calls) >= 3 else None
    service.candidate_check = gate
    result = service.publish(i, authorization(i), None)
    assert result['status'] == 'blocked' and remote.writes == ['push'] and not remote.pulls


def test_lost_push_before_remote_effect_retries_only_after_readback(publisher):
    service, remote, _ = publisher; i = make_intent()
    original = remote.push
    def failed(b, i):
        remote.push = original
        raise ConfigError('publication_outcome_unknown')
    remote.push = failed
    assert service.publish(i, authorization(i), None)['status'] == 'unknown'
    assert i.head_branch not in remote.refs
    result = service.publish(i, authorization(i), None)
    assert result['status'] == 'published' and remote.writes == ['push', 'create_pr']


def test_pr_appearing_after_push_is_reconciled_before_create(publisher):
    service, remote, _ = publisher; i = make_intent()
    original = remote.push
    def pushed(b, i):
        original(b, i); remote.create_pr(b, i)
    remote.push = pushed
    result = service.publish(i, authorization(i), None)
    assert result['status'] == 'published' and len(remote.pulls) == 1
    assert remote.writes == ['push', 'create_pr']
