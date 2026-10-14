import json
from pathlib import Path

import pytest
import jsonschema

from harness_local.cli import main
from harness_core.distribution import MODELS


@pytest.mark.parametrize('argv,code,status',[
    (['bootstrap','--json'],0,'partial'),
    (['release','candidate','--json'],0,'partial'),
    (['release','gate','--input','docs/evidence/distribution/pending-pilot-report.json','--json'],1,'blocked'),
    (['release','gate','--json'],2,'invalid'),
    (['update','apply','--json'],2,'invalid'),
])
def test_cli_envelope(argv,code,status,capsys):
    assert main(argv)==code
    result=json.loads(capsys.readouterr().out)
    assert result['schema_version']==1 and 'checks' in result
    if code in (0,1): assert result['status']==status
    if code==0: assert not result['certified'] and not result['release_allowed']


def test_packaged_schemas_and_examples():
    from importlib.resources import files
    for model in MODELS:
        name=model.__name__.lower()+'.schema.json'
        assert json.loads(files('harness_core').joinpath('schemas/'+name).read_bytes())==model.model_json_schema()
        example=Path('docs/examples/distribution')/(model.__name__.lower()+'.json')
        if example.exists():
            value=json.loads(example.read_bytes())
            jsonschema.validate(value,model.model_json_schema())
            model.model_validate(value)


def test_resource_drift_rejected(scratch,monkeypatch):
    import harness_local.distribution as module
    manifest=module.candidate_manifest()
    name=next(iter(manifest.resources))
    (scratch/'distribution_kit').mkdir()
    (scratch/'distribution_kit/candidate.json').write_text(json.dumps(manifest.model_dump()))
    path=scratch/name
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(b'tampered')
    monkeypatch.setattr(module,'files',lambda _:scratch)
    from harness_core.configuration import ConfigError
    with pytest.raises(ConfigError,match='distribution_resource_drift'): module.candidate_manifest()
