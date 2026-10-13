import json
from pathlib import Path

import jsonschema

from harness_core.hu import HuRun, PlanRevision, ApprovalRecord, Candidate, Assignment, GateResult
from test_hu_lifecycle import hu, approved, candidate


def test_hu_examples_match_shipped_schemas(hu):
    service,client,_=hu
    run=approved(service)['run']
    c=candidate(service,client)
    run=service.run('status','HU1')['run']
    values={HuRun:run,PlanRevision:run['plan'],ApprovalRecord:run['approval'],Candidate:c,
        Assignment:dict(schema_version=1,role='developer',actor='writer',write_paths=['src/total.py'],isolation='checkout',delegation_depth=0),
        GateResult:dict(schema_version=1,gate='validation',status='blocked',reason='not_run',candidate_sha256=c['candidate_sha256'])}
    for model,value in values.items():
        schema=json.loads(Path('src/harness_core/schemas',model.__name__.lower()+'.schema.json').read_text())
        jsonschema.validate(value,schema)
        jsonschema.validate(value,json.loads(Path('schemas',model.__name__.lower()+'.schema.json').read_text()))


def test_hu_resource_loading_and_rendering():
    from harness_local.desktop_resources import load_desktop,resources,render_integration
    from harness_core.desktop import activate_profiles
    catalog=activate_profiles(load_desktop(),{'principal':{'model':'test-model','effort':'medium'}},{'test-model':['medium']})
    rendered=render_integration(catalog)
    assert rendered['.agents/skills/harness-hu/SKILL.md']==resources()['harness-hu/SKILL.md']
    assert rendered['.codex/agents/harness-principal.toml']
