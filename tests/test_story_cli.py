import json
from pathlib import Path

import pytest

from harness_local.cli import main
from test_publication import make_intent, authorization
from test_hu_lifecycle import hu


def pending():
    request = json.loads(Path('docs/evidence/observability-evals/pending-batch.json').read_text())
    request.update(milestone=7, budget_runs=144)
    return request


def test_provider_evaluations_remain_pending_with_real_scorer():
    from harness_local.evaluation_service import dispatch
    from harness_local.publication import evaluation_gate
    report, code = dispatch('report', pending())
    assert code == 1 and report['required_runs'] == 144
    rows = report['profiles'][0]['matrix']
    assert len([r for r in rows if r['case_id'] in ('E21', 'E22', 'E23')]) == 9
    assert all(r['status'] == 'not_run' for r in rows)
    assert evaluation_gate(pending()) == 'required_evaluations_blocked'


@pytest.mark.parametrize('status', ['not_run', 'blocked'])
def test_cli_preview_pending_evals_never_authenticates_or_writes(scratch, capsys, monkeypatch, status):
    i = make_intent(); source = scratch / 'request.json'
    evaluation = pending()
    if status == 'blocked':
        from harness_core.onboarding_plan import sha, canonical
        evaluation['runs'] = [dict(schema_version=1,run_id='blocked1',case_id='E21',role='principal',
            profile_sha256=sha(canonical(evaluation['profiles'][0])),repetition=1,surface='desktop',mode='manual',
            status='blocked',observed_at='2026-10-13T00:00:00Z',duration_ms=None,artifact_ref=None,
            artifact_sha256=None,output=None,simulated=False)]
    source.write_text(json.dumps(dict(schema_version=1, intent=i.model_dump(),
        authorization=authorization(i).model_dump(), evaluation=evaluation)))
    import harness_local.story_providers as providers
    monkeypatch.setattr(providers, 'select_provider', lambda *a, **k: pytest.fail('preview called provider'))
    before = source.read_bytes()
    assert main(['pr', 'preview', '--input', str(source), '--json']) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['publication_gate'] == 'blocked' and result['reason'] == 'required_evaluations_blocked'
    assert source.read_bytes() == before and list(scratch.iterdir()) == [source]


def test_cli_fixture_read_requires_external_binding_and_does_not_create_state(scratch, capsys):
    from harness_core.story import ProviderBinding
    raw = dict(schema_version=1, client_id='alpha', checkout_id='checkout', provider='fixture', transport='fixture',
        repository='demo/alpha', base_branch='develop', capabilities=['read_story'])
    source = scratch / 'provider.json'; source.write_text(json.dumps(raw))
    assert main(['story', 'read', '--provider', str(source), '--source', '17', '--json']) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['snapshot']['source_id'] == '17' and result['simulated'] and not result['certified']
    assert list(scratch.iterdir()) == [source]


def test_cli_publish_missing_configuration_has_no_effects(scratch, capsys):
    i = make_intent(); source = scratch/'request.json'
    source.write_text(json.dumps(dict(schema_version=1, intent=i.model_dump(), authorization=None, evaluation=None)))
    assert main(['pr', 'publish', '--input', str(source), '--json']) == 2
    assert json.loads(capsys.readouterr().out)['command'] == 'pr'


@pytest.mark.parametrize('kind', ['unchanged', 'spec_after_approval', 'context_after_approval', 'mode_after_approval', 'crlf', 'unbound_story', 'changed_story'])
def test_final_committed_candidate_rechecked_after_openspec_changes(hu, kind):
    from harness_core.story import intent, snapshot
    from harness_local.publication import candidate_gate
    from test_hu_lifecycle import plan, git
    service, client, preparation = hu
    if kind == 'crlf':
        git(client['target'],'config','core.autocrlf','true')
        # A baseline file has CRLF in the approved checkout but LF in Git.
        f=client['target']/'README.local.md'; f.write_bytes(b'Baseline\r\n')
        git(client['target'],'add','README.local.md')
        git(client['target'],'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','CRLF baseline')
    service.run('start','FINAL','start',dict(schema_version=1,writer_actor='developer',onboarding_plan=str(preparation),simulation=False))
    p = plan(service)  # HU1 is unrelated; FINAL keeps its own approval and evidence.
    raw = p['run']['plan']; fields = ['criteria','paths','operations','tests','required_capabilities','max_delegations','allow_worktrees','sources','decisions']
    p = service.run('plan','FINAL','p',dict(schema_version=1, **{k:raw[k] for k in fields}))['run']['plan']
    service.run('approve','FINAL','a',dict(schema_version=1,actor='operator',confirmed=True,client_id='alpha',checkout_id='checkout',attempt=1,revision=1,plan_sha256=p['plan_sha256']))
    story = snapshot('demo/alpha','17','r','Sumar',['x'],[])
    if kind != 'unbound_story':
        from harness_local.publication import bind_story
        from harness_core.story import StoryPlanBinding
        bind_story(service,StoryPlanBinding(schema_version=1,client_id='alpha',checkout_id='checkout',hu_id='FINAL',attempt=1,
            plan_sha256=p['plan_sha256'],actor='operator',confirmed=True,story=story))
        if kind == 'changed_story':
            from harness_core.configuration import ConfigError
            with pytest.raises(ConfigError,match='story_plan_binding_immutable'):
                bind_story(service,StoryPlanBinding(schema_version=1,client_id='alpha',checkout_id='checkout',hu_id='FINAL',attempt=1,
                    plan_sha256=p['plan_sha256'],actor='operator',confirmed=True,
                    story=snapshot('demo/alpha','17','r2','Sumar',['nuevo'],[])))
    (client['target']/'src').mkdir(exist_ok=True)
    (client['target']/'src/total.py').write_bytes(b'def total(xs): return sum(xs)\r\n' if kind=='crlf' else b'def total(xs): return sum(xs)\n')
    c = service.run('candidate','FINAL','c',dict(schema_version=1))['run']['candidate']
    service.run('transition','FINAL','v',dict(schema_version=1,state='validating'))
    for eid, who, kind_e in [('T16','tester','test'), ('review','auditor','review')]:
        service.run('evidence','FINAL',eid,dict(schema_version=1,id=eid,actor=who,kind=kind_e,status='passed',simulated=False,
            candidate_sha256=c['candidate_sha256'],evidence_ref=eid))
    service.run('transition','FINAL','r',dict(schema_version=1,state='reviewing'))
    assert service.run('transition','FINAL','ready',dict(schema_version=1,state='ready_to_publish'))['status'] == 'ready'
    if kind == 'spec_after_approval':
        d=client['target']/'openspec'; d.mkdir(exist_ok=True); (d/'extra.md').write_text('Nueva spec')
    if kind == 'context_after_approval':
        d=client['target']/'.harness/context.md'; d.write_text(d.read_text()+'\nNueva regla')
    git(client['target'],'add','.')
    if kind == 'mode_after_approval': git(client['target'],'update-index','--chmod=+x','src/total.py')
    git(client['target'],'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','final')
    head=git(client['target'],'rev-parse','HEAD').decode().strip()
    i=intent(intent_id='final1',client_id='alpha',checkout_id='checkout',hu_id='FINAL',attempt=1,provider='github',
        repository='demo/alpha',base_branch='develop',head_branch='feature/final',base_oid=c['base'],head_oid=head,
        candidate_sha256=c['candidate_sha256'],context_sha256=c['context_sha256'],plan_sha256=p['plan_sha256'],
        story=snapshot('demo/alpha','17','r2','Sumar',['nuevo'],[]) if kind=='changed_story' else story,
        title='Sumar',body='Evidencia T16',evidence_refs=['T16','review'])
    assert candidate_gate(service,i) == {'unchanged':None,'spec_after_approval':'candidate_changed',
        'context_after_approval':'context_changed','mode_after_approval':'candidate_changed','crlf':None,
        'unbound_story':'story_plan_binding_required','changed_story':'story_plan_binding_mismatch'}[kind]
