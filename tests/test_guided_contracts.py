import json

import pytest
from pydantic import ValidationError

from harness_core.configuration import ConfigError
from harness_core.guided import ClientDevelopmentConfig, ClientToolBinding, QuestionnaireDraft, collect


def development():
    return dict(schema_version=1, client_id='alpha', stack=['Python'], conventions=['pytest'],
        business_rules=['Sumar amount no null en COP por día UTC; decimal exacto.'],
        roles=['auditor'], validations=['pytest'], sources={'business_rules': 'user', 'stack': 'template'})


def test_complete_template_no_redundant_questions():
    values = dict(target_path='C:/client', policy_path='C:/policy.json', binding_path='C:/binding.json',
        development=development(), tool_binding=dict(schema_version=1, client_id='alpha', checkout_id='checkout', tools=[]),
        catalog={'selected': 'explicit'})
    draft = QuestionnaireDraft(schema_version=1, answers={k: dict(value=v, status='known', source='template', confirmed=True) for k,v in values.items()})
    result = collect(draft)
    assert result['questions'] == []
    assert result['values']['development']['business_rules'] == values['development']['business_rules']


def test_interview_missing_and_unconfirmed_fields():
    draft = QuestionnaireDraft(schema_version=1, answers={'target_path': dict(value='C:/a', status='known', source='local', confirmed=False)})
    result = collect(draft)
    assert 'target_path' in {q['field'] for q in result['questions']}
    assert all(q['requirement'] == 'required' for q in result['questions'])
    assert collect(QuestionnaireDraft(schema_version=1, answers={}))['status'] == 'blocked'


@pytest.mark.parametrize('secret', ['ghp_' + 'a'*24, 'password=hunter2', 'https://user:pass@example.com', 'Bearer abcdefghi'])
def test_secret_answers_rejected_without_echo(secret):
    with pytest.raises(ValidationError, match='secret_not_allowed') as error:
        QuestionnaireDraft(schema_version=1, answers={'target_path': dict(value=secret, status='known', source='user', confirmed=True)})
    assert secret not in str(error.value)


def test_separate_contracts_strict_version_and_no_secrets():
    config = ClientDevelopmentConfig.model_validate(development())
    assert 'checkout_id' not in config.model_dump()
    with pytest.raises(ValidationError): ClientDevelopmentConfig.model_validate({**development(), 'checkout_id': 'other'})
    with pytest.raises(ValidationError): ClientDevelopmentConfig.model_validate({**development(), 'schema_version': 2})
    with pytest.raises(ValidationError): ClientToolBinding(schema_version=1, client_id='alpha', checkout_id='checkout',
        tools=[dict(id='sql', kind='mcp', connection_ref='https://user:pass@example.com', status='not_checked')])


def test_generated_schemas_match_examples():
    from pathlib import Path
    import jsonschema
    models = [ClientDevelopmentConfig, ClientToolBinding, QuestionnaireDraft]
    for model in models:
        schema = json.loads(Path('src/harness_core/schemas', model.__name__.lower()+'.schema.json').read_text())
        assert schema == model.model_json_schema()
    jsonschema.validate(development(), ClientDevelopmentConfig.model_json_schema())


def test_packaged_templates_and_dependency_receipt_match_schemas():
    from harness_local.guided_resources import resources
    from harness_core.guided import GuidedRequest
    from pathlib import Path
    import jsonschema
    bundle=resources()
    incomplete=QuestionnaireDraft.model_validate(json.loads(bundle['questionnaire.json']))
    assert collect(incomplete)['questions']
    complete=json.loads(bundle['complete-template.json'])
    jsonschema.validate(complete,QuestionnaireDraft.model_json_schema())
    request=GuidedRequest.model_validate(dict(schema_version=1,**collect(QuestionnaireDraft.model_validate(complete))['values']))
    jsonschema.validate(request.model_dump(),GuidedRequest.model_json_schema())
    receipt=json.loads(bundle['dependency.json'])
    from harness_core.onboarding_plan import sha
    assert receipt['status']=='verified-supervised' and not receipt['strict_certified']
    for path,expected in receipt['evidence'].items(): assert sha(Path(path).read_bytes())==expected
