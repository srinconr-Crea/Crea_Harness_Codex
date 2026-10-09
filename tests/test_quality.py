"""Boundary tests: corrupted resources, unsafe extensions and invented outcomes."""
import hashlib
import json
import shutil
from decimal import Decimal
from importlib.resources import files
from pathlib import Path

import pytest


def api():
    from harness_core import quality
    from harness_local import quality_resources
    return quality, quality_resources


def definitions():
    return {name: json.loads(Path(f'docs/planning/quality/{name}.json').read_text(encoding='utf-8'))
            for name in ('practices', 'test-cases', 'eval-cases')}


def test_loads_complete_offline_catalogs_and_selects_pyspark():
    q, resources = api()
    bundle = resources.load_quality()
    assert len(bundle.practices.rules) == 32
    assert len(bundle.tests.cases) == len(bundle.evals.cases) == 24
    plan = q.resolve_practices(bundle.practices, 'pyspark')
    assert 'SP-01' in {r.id for r in plan.rules}
    assert all(r.technology in ('general', 'pyspark') for r in plan.rules)
    assert all(r.execution_status == 'not_run' for r in plan.rules)
    assert all(r.severity == 'advisory' for r in plan.rules if r.id in ('SP-03', 'SP-04'))
    assert bundle.evals.cases[0].observed_output is None
    assert bundle.dataset_sha256 == hashlib.sha256(bundle.fixture_bytes).hexdigest()


@pytest.mark.parametrize('mutation', ['version', 'boolean_version', 'unknown', 'duplicate_rule',
    'missing_source', 'case_limit', 'duplicate_case', 'missing_rule', 'duplicate_check',
    'invented_score', 'invented_output', 'passed_definition', 'fixture_traversal', 'missing_check'])
def test_invalid_definitions_fail_before_any_execution(mutation):
    q, _ = api()
    d = definitions()
    if mutation == 'version': d['practices']['schema_version'] = 2
    if mutation == 'boolean_version': d['practices']['schema_version'] = True
    if mutation == 'unknown': d['practices']['permissions'] = ['publish']
    if mutation == 'duplicate_rule': d['practices']['rules'].append(d['practices']['rules'][0])
    if mutation == 'missing_source': d['practices']['rules'][0]['source_refs'] = ['missing']
    if mutation == 'case_limit': d['test-cases']['cases'] *= 11
    if mutation == 'duplicate_case': d['test-cases']['cases'].append(d['test-cases']['cases'][0])
    if mutation == 'missing_rule': d['test-cases']['cases'][0]['source_rules'] = ['missing']
    if mutation == 'duplicate_check':
        d['eval-cases']['cases'][0]['expected']['checks'].append(d['eval-cases']['cases'][0]['expected']['checks'][0])
    if mutation == 'invented_score': d['eval-cases']['cases'][0]['scores'] = {'passed': 1}
    if mutation == 'invented_output': d['eval-cases']['cases'][0]['observed_output'] = 'success'
    if mutation == 'passed_definition': d['test-cases']['cases'][0]['status'] = 'passed'
    if mutation == 'fixture_traversal': d['test-cases']['fixture_ref'] = '../secrets.json'
    if mutation == 'missing_check': d['eval-cases']['cases'][0]['expected']['checks'] = []
    with pytest.raises(ValueError): q.validate_catalogs(d['practices'], d['test-cases'], d['eval-cases'])


@pytest.mark.parametrize('mode', ['alter', 'missing', 'manifest_traversal', 'wrong_commit', 'omit_license'])
def test_tampered_resources_rejected(scratch, mode):
    _, resources = api()
    root = scratch / 'quality'
    shutil.copytree(str(files('harness_local').joinpath('quality_kit')), root)
    target = root / 'vendor/databricks-agent-skills/skills/databricks-core/SKILL.md'
    if mode == 'alter': target.write_bytes(b'tampered')
    if mode == 'missing': target.unlink()
    if mode == 'manifest_traversal':
        p = root / 'manifest.json'
        d = json.loads(p.read_bytes()); d['files'][0]['path'] = '../outside'; p.write_text(json.dumps(d))
    if mode in ('wrong_commit', 'omit_license'):
        p = root / 'vendor/databricks-agent-skills/SOURCE.json'
        d = json.loads(p.read_bytes())
        if mode == 'wrong_commit': d['commit'] = '0' * 40
        else: d['files'] = [f for f in d['files'] if f['path'] != 'LICENSE']
        p.write_text(json.dumps(d))
    with pytest.raises(ValueError): resources.load_quality(root)


def test_document_limit_duplicate_json_and_error_redaction(scratch):
    q, _ = api()
    p = scratch / 'catalog.json'
    p.write_bytes(b' ' * (1024 * 1024 + 1))
    with pytest.raises(ValueError, match='document_too_large'): q.load_definition(p, q.PracticePack)
    p.write_text('{"schema_version":1,"schema_version":1}')
    with pytest.raises(ValueError, match='duplicate_key'): q.load_definition(p, q.PracticePack)
    p.write_text('{"schema_version":2,"private_key":"sensitive-value"}')
    with pytest.raises(ValueError) as error: q.load_definition(p, q.PracticePack)
    assert 'sensitive-value' not in str(error.value)


def extension(pack):
    rule = pack.rules[0].model_dump()
    rule.update(id='CLIENT-01', technology='pyspark', statement='Comprobar unicidad de salida')
    return dict(schema_version=1, client_id='alpha', base_pack_id=pack.pack_id,
                base_version=pack.version, sources=[], rules=[rule],
                strengthen=[dict(rule_id='SP-01', additional_evidence=['Prueba de esquema'])], exceptions=[])


def test_extension_adds_and_strengthens_without_mutating_base_or_policy():
    q, resources = api()
    pack = resources.load_quality().practices
    before = pack.model_dump()
    plan = q.resolve_practices(pack, 'pyspark', extension(pack), client_id='alpha')
    assert 'CLIENT-01' in {r.id for r in plan.rules}
    assert plan.additional_evidence['SP-01'] == ['Prueba de esquema']
    assert pack.model_dump() == before
    assert 'CLIENT-01' not in {r.id for r in q.resolve_practices(pack, 'pyspark').rules}


@pytest.mark.parametrize('mutation', ['client', 'version', 'replace', 'permissions', 'skip_gate', 'unreviewed', 'unknown_rule'])
def test_extension_conflicts_and_policy_bypass_rejected(mutation):
    q, resources = api()
    pack = resources.load_quality().practices
    ext = extension(pack)
    if mutation == 'client': ext['client_id'] = 'beta'
    if mutation == 'version': ext['base_version'] = 'different'
    if mutation == 'replace': ext['rules'][0]['id'] = pack.rules[0].id
    if mutation == 'permissions': ext['allowed_paths'] = ['private/']
    if mutation == 'skip_gate': ext['skip_approval'] = True
    if mutation == 'unknown_rule': ext['strengthen'][0]['rule_id'] = 'missing'
    if mutation == 'unreviewed': ext['exceptions'] = [dict(rule_id='SP-01', reason='legacy', scope='migration')]
    with pytest.raises(ValueError): q.resolve_practices(pack, 'pyspark', ext, client_id='alpha')


def test_reviewed_exception_applies_only_to_selected_scope():
    q, resources = api()
    pack = resources.load_quality().practices
    ext = extension(pack)
    ext['exceptions'] = [dict(rule_id='SP-01', reason='legacy', scope='migration',
                              reviewed_by='reviewer', decision_ref='DEC-01')]
    assert not q.resolve_practices(pack, 'pyspark', ext, client_id='alpha', scope='new').exceptions
    plan = q.resolve_practices(pack, 'pyspark', ext, client_id='alpha', scope='migration')
    assert plan.exceptions[0].decision_ref == 'DEC-01'
    assert 'SP-01' in {r.id for r in plan.rules}


def test_fixture_paths_resolve_and_missing_fixture_blocks_loading(scratch):
    q, _ = api()
    (scratch / 'fixtures').mkdir()
    with pytest.raises(ValueError, match='fixture_missing'):
        q.load_fixture(scratch, 'fixtures/absent.json')
    for path in ('../outside', 'C:/outside', '/outside', 'fixtures\\outside'):
        with pytest.raises(ValueError): q.load_fixture(scratch, path)


def test_synthetic_oracles_are_independent_of_agent_outputs():
    _, resources = api()
    data = json.loads(resources.load_quality().fixture_bytes)
    orders = data['orders']
    assert sum((Decimal(o['amount']) for o in orders if o['amount'] is not None), Decimal(0)) == Decimal('30.00')
    join = [o for o in orders for c in data['customers_duplicate'] if o['customer_id'] == c['customer_id']]
    assert len(join) == 5
    assert sum((Decimal(o['amount']) for o in join if o['amount'] is not None), Decimal(0)) == Decimal('40.00')


def test_definition_report_never_certifies_runtime_or_agent():
    q, resources = api()
    bundle = resources.load_quality()
    report = q.definition_report(bundle.evals, available_modes=set())
    assert report['status'] == 'blocked'
    assert report['execution_status'] == 'not_run'
    assert report['observed_output'] is None
    assert q.definition_report(bundle.evals, available_modes={'desktop-manual-first'})['status'] == 'not_run'
    assert {c.split for c in bundle.evals.cases} == {'golden', 'holdout'}


def test_rubric_rejects_missed_defect_and_false_positive():
    q, resources = api()
    cases = resources.load_quality().evals.cases
    defect = next(c for c in cases if c.expected.known_defects)
    clean = next(c for c in cases if not c.expected.known_defects)
    assert q.compare_findings(defect, [])['passed'] is False
    assert q.compare_findings(clean, ['invented-defect'])['passed'] is False
    assert q.compare_findings(clean, [])['passed'] is True


def test_schema_examples_and_rejections_agree_with_models():
    from jsonschema import Draft202012Validator
    q, _ = api()
    for name, model, schema in [('practices', q.PracticePack, 'practicepack'),
                               ('test-cases', q.TestCatalog, 'testcatalog'),
                               ('eval-cases', q.EvalCatalog, 'evalcatalog')]:
        validator = Draft202012Validator(json.loads(files('harness_core').joinpath(f'schemas/{schema}.schema.json').read_bytes()))
        valid = definitions()[name]
        validator.validate(valid)
        assert model.model_validate(valid)
        for invalid in (dict(valid, schema_version=2), dict(valid, unexpected=True)):
            assert list(validator.iter_errors(invalid))
            with pytest.raises(ValueError): model.model_validate(invalid)


def test_secret_container_key_and_oversized_programmatic_definition_rejected():
    q, _ = api()
    d = definitions()
    d['eval-cases']['cases'][0]['input']['password'] = {'value': 'private'}
    with pytest.raises(ValueError):
        q.decode_definition(json.dumps(d['eval-cases']).encode(), q.EvalCatalog)
    huge = definitions()
    huge['eval-cases']['cases'][0]['input']['long'] = 'x' * (1024 * 1024)
    with pytest.raises(ValueError): q.validate_catalogs(huge['practices'], huge['test-cases'], huge['eval-cases'])
