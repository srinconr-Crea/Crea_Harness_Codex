import json

from harness_local.cli import main
from test_environment_setup import supplied


def test_setup_cli_interview_preview_and_stale_approval(client,scratch,capsys):
    data=scratch/'setup.json'; data.write_text(json.dumps(supplied(client)),encoding='utf-8')
    assert main(['setup','interview','--input',str(data),'--json'])==0
    assert json.loads(capsys.readouterr().out)['questions']==[]
    parent=scratch/'parent.json'
    code=main(['setup','preview','--input',str(data),'--plan-out',str(parent),'--json'])
    output=json.loads(capsys.readouterr().out)
    assert code in (0,4) and 'plan' in output
    assert main(['setup','apply','--plan',str(parent),'--authorize','0'*64,'--json'])==4
    assert json.loads(capsys.readouterr().out)['reason']=='plan_stale'


def test_setup_cli_invalid_secret_is_redacted(scratch,capsys):
    secret='ghp_'+'x'*24
    data=scratch/'setup.json'; data.write_text(json.dumps({'schema_version':1,'repository_url':'https://'+secret+'@github.com/demo/alpha.git'}))
    assert main(['setup','interview','--input',str(data),'--json'])==2
    assert secret not in capsys.readouterr().out
