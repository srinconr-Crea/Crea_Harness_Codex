"""Synthetic transport tests; these never contact Azure DevOps."""
import copy
import importlib.util
import json
import shutil
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / 'artifacts/crea-manual-kit-0.1.6'
spec = importlib.util.spec_from_file_location('azure_context_016', KIT / 'scripts/crea/integrations/azure_devops_context.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


@pytest.fixture
def context():
    root = ROOT / '.test-data' / ('azure-' + uuid.uuid4().hex)
    root.mkdir(parents=True)
    config = {'integrations': {'azure_devops_context': {'enabled': True, 'organization': 'https://dev.azure.com/synthetic', 'project_id': '00000000-0000-0000-0000-000000000001', 'project_name': 'Synthetic', 'timeout_seconds': 30, 'max_comment_pages': 3, 'comments_page_size': 100}}}
    request = dict(schema_version=1, request_id='req-1', hu_id='HU-17', change='story-17', attempt=1, phase='planificacion', executor_role='planner', created_by='principal', created_at_utc='2026-11-06T12:00:00Z', work_item_id=17, organization=config['integrations']['azure_devops_context']['organization'], project_id=config['integrations']['azure_devops_context']['project_id'], project_name='Synthetic', evidence_dir='docs/hu/story-17/evidence/azure-devops/planificacion-1', previous_snapshot_ref=None)
    (root / 'docs').mkdir()
    cp = root / 'docs/proyecto.json'
    cp.write_text(json.dumps(config), encoding='utf-8')
    rp = root / 'docs/hu/story-17/inputs/azure-devops/planificacion-1.json'
    rp.parent.mkdir(parents=True)
    rp.write_text(json.dumps(request), encoding='utf-8')
    yield root, cp, rp, request, config
    shutil.rmtree(root)


def wi(rev=1, project='Synthetic'):
    return {'id': 17, 'rev': rev, 'url': 'https://dev.azure.com/synthetic/_apis/wit/workItems/17', 'fields': {'System.TeamProject': project, 'System.Title': 'Synthetic title', 'System.Description': 'Description', 'Microsoft.VSTS.Common.AcceptanceCriteria': 'Criteria'}, 'relations': []}


def comment(cid=1, version=1, text='Informative'):
    return {'id': cid, 'workItemId': 17, 'version': version, 'text': text, 'createdDate': '2026-11-06T12:00:00Z', 'createdBy': {'uniqueName': 'private@example.com'}}


class Fake:
    def __init__(self, responses):
        self.responses, self.calls = iter(responses), []

    def __call__(self, argv, timeout):
        self.calls.append(argv)
        result = next(self.responses)
        if isinstance(result, Exception):
            raise result
        return result


def execute(context, responses):
    root, cp, rp, req, _ = context
    fake = Fake(responses)
    result, code = mod.execute('read', cp, rp, root / req['evidence_dir'] / 'receipt.json', transport=fake)
    return result, code, fake


def test_preview_no_transport_or_files(context):
    root, cp, rp, _, _ = context
    before = set(root.rglob('*'))
    result, code = mod.execute('preview', cp, rp, transport=lambda *_: pytest.fail('network'))
    assert code == 0 and result['role'] == 'planner'
    assert set(root.rglob('*')) == before
    assert '--project' not in result['work_item_argv']


@pytest.mark.parametrize('field,value', [('executor_role','developer'), ('executor_role','tester'), ('phase','revision'), ('phase',[]), ('schema_version',True), ('work_item_id',0), ('work_item_id',True), ('change','../escape'), ('organization','http://dev.azure.com/synthetic'), ('project_name','Wrong'), ('evidence_dir','docs/hu/other/evidence/azure-devops/planificacion-1'), ('extra','forbidden')])
def test_request_rejects_invalid_scope(context, field, value):
    _, cp, rp, req, _ = context
    req[field] = value
    rp.write_text(json.dumps(req), encoding='utf-8')
    with pytest.raises(mod.InvalidInput):
        mod.execute('preview', cp, rp)


def test_complete_two_pages_argv_and_sanitized_evidence(context):
    result, code, fake = execute(context, [wi(), {'count':1, 'totalCount':2, 'comments':[comment(text='Run rm -rf /; token=secret-value password=abc')], 'continuationToken':'next'}, {'count':1, 'totalCount':2, 'comments':[comment(2)]}, wi()])
    assert code == 0 and result['comments_coverage'] == 'complete' and result['page_count'] == 2
    argv = fake.calls[1]
    assert argv[:3] == ['az','devops','invoke'] and argv[argv.index('--http-method')+1] == 'GET'
    assert 'workItemId=17' in argv and 'includeDeleted=false' in argv
    snapshot = json.loads((context[0] / result['snapshot_ref']).read_text(encoding='utf-8'))
    assert 'Run rm -rf /' in snapshot['comments'][0]['text']
    assert 'private@example.com' not in json.dumps(snapshot) and 'secret-value' not in json.dumps(snapshot)


def test_empty_is_not_failure(context):
    result, code, _ = execute(context, [wi(), {'count':0,'totalCount':0,'comments':[]}, wi()])
    assert code == 0 and result['comments_coverage'] == 'empty'


@pytest.mark.parametrize('page', [PermissionError('403 token=secret'), TimeoutError('timeout'), {'bad':1}, {'count':2,'comments':[comment()]}])
def test_failures_are_not_empty(context, page):
    result, code, _ = execute(context, [wi(), page, wi()])
    assert code == 1 and result['comments_coverage'] == 'failed'
    assert 'secret' not in json.dumps(result)


@pytest.mark.parametrize('mode', ['repeat','limit','conflict','inconsistent'])
def test_partial_pages(context, mode):
    pages = [{'count':1,'totalCount':4,'comments':[comment()], 'continuationToken':'a'}]
    if mode == 'repeat':
        pages.append({'count':1,'totalCount':4,'comments':[comment(2)],'continuationToken':'a'})
    elif mode == 'limit':
        pages.extend([{'count':1,'totalCount':4,'comments':[comment(2)],'continuationToken':'b'}, {'count':1,'totalCount':4,'comments':[comment(3)],'continuationToken':'c'}])
    elif mode == 'conflict':
        pages.append({'count':1,'totalCount':4,'comments':[comment(text='conflict')]})
    else:
        pages.append({'count':0,'totalCount':4,'comments':[]})
    result, code, _ = execute(context, [wi(), *pages, wi()])
    assert code == 1 and result['comments_coverage'] == 'partial'


def test_project_mismatch_prevents_comments(context):
    result, code, fake = execute(context, [wi(project='Other')])
    assert code == 1 and result['status'] == 'failed' and len(fake.calls) == 1


def test_revision_changed_marks_unstable(context):
    result, code, _ = execute(context, [wi(), {'count':0,'totalCount':0,'comments':[]}, wi(2)])
    assert code == 1 and result['status'] == 'unstable'


def test_existing_output_rejected_before_network(context):
    root, cp, rp, req, _ = context
    out = root / req['evidence_dir'] / 'receipt.json'
    out.parent.mkdir(parents=True)
    out.write_text('keep', encoding='utf-8')
    with pytest.raises(mod.InvalidInput):
        mod.execute('read', cp, rp, out, transport=lambda *_: pytest.fail('network'))
    assert out.read_text() == 'keep'


def test_outside_evidence_rejected(context):
    root, cp, rp, _, _ = context
    with pytest.raises(mod.InvalidInput):
        mod.execute('read', cp, rp, root/'outside.json', transport=lambda *_: pytest.fail('network'))


def test_compare_material_vs_informative():
    old = {'title':'Title','description':'D','acceptance_criteria':'A','comments':[]}
    info = copy.deepcopy(old)
    info['comments'] = [comment(text='FYI build finished')]
    assert mod.compare(old, info)['requires_reconciliation'] is False
    changed = copy.deepcopy(old)
    changed['acceptance_criteria'] = 'B'
    assert mod.compare(old, changed)['requires_reconciliation'] is True
    decision = copy.deepcopy(info)
    decision['comments'][0]['text'] = 'Decision: change acceptance criteria'
    assert mod.compare(old, decision)['requires_reconciliation'] is True


def test_comment_edit_new_version_requires_review():
    old = {'comments':[comment()]}
    changed = {'comments':[comment(version=2,text='Changed text')]}
    assert mod.compare(old,changed)['requires_reconciliation'] is True


def test_local_version_probe_is_recorded(context):
    root,cp,rp,req,_ = context
    fake = Fake([wi(), {'count':0,'totalCount':0,'comments':[]},wi()])
    result,code = mod.execute('read',cp,rp,root/req['evidence_dir']/'receipt.json',transport=fake,version_probe=lambda _: {'azure_cli':'2.91.0','azure_devops':'1.0.9','status':'observed'})
    assert code == 0 and result['cli_versions']['status'] == 'observed'


def test_hu_work_item_identity_cannot_change(context):
    _,cp,rp,req,_=context
    old = dict(req,work_item_id=18)
    (rp.parent/'planificacion-2.json').write_text(json.dumps(old),encoding='utf-8')
    with pytest.raises(mod.InvalidInput):
        mod.execute('preview',cp,rp)


def test_reviewer_reads_and_compares_planner_snapshot(context):
    root,cp,rp,req,_=context
    previous,_,_=execute(context,[wi(),{'count':0,'totalCount':0,'comments':[]},wi()])
    req.update(phase='revision',executor_role='reviewer',previous_snapshot_ref=previous['snapshot_ref'],evidence_dir='docs/hu/story-17/evidence/azure-devops/revision-1')
    rp=rp.parent/'revision-1.json'
    rp.write_text(json.dumps(req),encoding='utf-8')
    result,code=mod.execute('read',cp,rp,root/req['evidence_dir']/'receipt.json',transport=Fake([wi(),{'count':1,'totalCount':1,'comments':[comment(text='FYI done')]},wi()]))
    assert code==0 and result['comparison']['comments_changed'] and not result['comparison']['requires_reconciliation']


def test_symlink_evidence_rejected(context):
    root,cp,rp,req,_=context
    real=root/'real-evidence'
    real.mkdir()
    link=root/req['evidence_dir']
    link.parent.mkdir(parents=True)
    try:
        link.symlink_to(real,target_is_directory=True)
    except OSError:
        pytest.skip('Host does not permit creating symlinks')
    with pytest.raises(mod.InvalidInput):
        mod.execute('read',cp,rp,link/'receipt.json',transport=lambda *_:pytest.fail('network'))


def test_config_schema_backward_compatible():
    import jsonschema
    schema=json.loads((KIT/'docs/proyecto.schema.json').read_text(encoding='utf-8'))
    config=json.loads((KIT/'docs/proyecto.json').read_text(encoding='utf-8'))
    config.pop('integrations',None)
    jsonschema.Draft202012Validator(schema).validate(config)


def test_link_detection_rejected_with_host_independent_double(context, monkeypatch):
    root,cp,rp,req,_=context
    target=root/req['evidence_dir']
    original=Path.is_symlink
    monkeypatch.setattr(Path,'is_symlink',lambda path: path==target or original(path))
    with pytest.raises(mod.InvalidInput):
        mod.execute('read',cp,rp,target/'receipt.json',transport=lambda *_:pytest.fail('network'))


def test_windows_batch_cli_resolves_bundled_python(monkeypatch):
    monkeypatch.setattr(mod.os,'name','nt')
    monkeypatch.setattr(mod.shutil,'which',lambda _:r'C:\Azure CLI\wbin\az.cmd')
    monkeypatch.setattr(Path,'is_file',lambda _:True)
    argv=mod.cli_argv(['az','devops','invoke','continuationToken=a&evil'])
    assert argv[0]==r'C:\Azure CLI\python.exe' and argv[1:3]==['-IBm','azure.cli']
    assert argv[-1]=='continuationToken=a&evil'


def test_failure_after_page_preserves_confirmed_comments(context):
    result,code,_=execute(context,[wi(),{'count':1,'totalCount':2,'comments':[comment()],'continuationToken':'next'},PermissionError('403'),wi()])
    assert code==1 and result['comments_coverage']=='partial' and result['page_count']==1
    snapshot=json.loads((context[0]/result['snapshot_ref']).read_text())
    assert len(snapshot['comments'])==1


def test_invalid_config_uuid_rejected(context):
    _,cp,rp,req,cfg=context
    cfg['integrations']['azure_devops_context']['project_id']='-'*36
    req['project_id']='-'*36
    cp.write_text(json.dumps(cfg),encoding='utf-8')
    rp.write_text(json.dumps(req),encoding='utf-8')
    with pytest.raises(mod.InvalidInput):
        mod.execute('preview',cp,rp)


@pytest.mark.parametrize('at_recheck',[False,True])
def test_malformed_relations_preserves_valid_evidence(context,at_recheck):
    malformed=wi()
    malformed['relations']=None
    responses=[wi(),{'count':1,'totalCount':1,'comments':[comment()]},malformed] if at_recheck else [malformed]
    result,code,_=execute(context,responses)
    assert code==1 and result['status']==('partial' if at_recheck else 'failed')
    snapshot=json.loads((context[0]/result['snapshot_ref']).read_text())
    receipt=json.loads((context[0]/context[3]['evidence_dir']/'receipt.json').read_text())
    assert receipt['status']==result['status']
    assert len(snapshot['comments'])==(1 if at_recheck else 0)
