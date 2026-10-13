import json

from harness_local.cli import main
from test_hu_lifecycle import hu, approved


def args(service, action, **fields):
    argv = ['hu',action,'--path',str(service.target),'--policy',str(service.policy_path),
        '--binding',str(service.binding_path),'--story','HU1','--json']
    for key, value in fields.items(): argv += ['--'+key,str(value)]
    return argv


def test_hu_cli_status_and_invalid_requests(hu, capsys):
    service, _, _ = hu
    assert main(args(service,'status')) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['command']=='hu' and result['run']['state']=='draft'
    assert result['publication_allowed'] is False and result['certified'] is False
    assert result['enforcement']=='kit commands/adapters only; external Desktop edits are detected at gates'
    assert main(args(service,'approve')) == 2
    assert json.loads(capsys.readouterr().out)['status']=='invalid'


def test_hu_cli_explicit_approval_and_block_codes(hu, capsys):
    service, client, _ = hu
    approved(service)
    request = client['policy'].parent / 'hu-request.json'
    request.write_text(json.dumps(dict(schema_version=1,state='published')))
    assert main(args(service,'transition',input=request,operation='publish')) == 1
    result = json.loads(capsys.readouterr().out)
    assert result['run']['blocked_reason']=='publication_unavailable'
    request.write_text(json.dumps(dict(schema_version=1,reason='password=DO_NOT_ECHO')))
    assert main(args(service,'block',input=request,operation='secret')) == 2
    assert 'DO_NOT_ECHO' not in capsys.readouterr().out


def test_hu_cli_human_output_after_mutation(hu,capsys):
    service,client,_=hu
    request=client['policy'].parent/'human.json'
    request.write_text(json.dumps(dict(schema_version=1,reason='tool_unavailable')))
    argv=args(service,'block',input=request,operation='human')
    argv.remove('--json')
    assert main(argv)==1
    output=capsys.readouterr().out
    assert 'HU1' in output and 'blocked' in output
