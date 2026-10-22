"""Pruebas del contrato; no requieren Databricks, Git remoto ni procesos de negocio."""
import copy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import shutil
import uuid
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / '.agents/skills/Crea/crea-pruebas/scripts/contract.py'
SPEC = importlib.util.spec_from_file_location('contract', SCRIPT)


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(cls.c)
        cls.policy = json.loads((ROOT / '.agents/skills/Crea/crea-pruebas/assets/policy.template.json').read_text(encoding='utf-8'))

    def setUp(self):
        scratch = (ROOT / '.test-work').resolve()
        self.root = scratch / uuid.uuid4().hex
        self.root.mkdir(parents=True)
        def cleanup():
            target = self.root.resolve()
            if target.parent != scratch or not target.is_relative_to(ROOT.resolve()):
                raise ValueError('Test cleanup escaped package')
            shutil.rmtree(target)
        self.addCleanup(cleanup)
        for name in ('src/pure.py', 'tests/test_pure.py', 'tests/fixtures/input.json', 'README.md'):
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('{}' if name.endswith('.json') else '# sample\n', encoding='utf-8')
        self.p = copy.deepcopy(self.policy)
        self.p['setup_complete'] = True
        self.p['checks'] = [{
            'id': 'unit', 'kind': 'pytest', 'environment': 'local', 'effect': 'local_execution',
            'argv': ['python', '-m', 'pytest', 'tests/test_pure.py'], 'configured': True,
            'timeout_seconds': 60, 'inputs': ['src/pure.py', 'tests/test_pure.py', 'tests/fixtures/input.json'],
            'criteria': ['CA01'], 'min_tests': 1, 'required_assertions': ['CA01'],
            'reuse_seconds': 3600
        }]
        self.p['rules'] = [
            {'id': 'DOC', 'paths': ['README.md'], 'checks': [], 'reason': 'Documento explicativo; requiere revisión documental.'},
            {'id': 'PURE', 'paths': ['src/pure.py', 'tests/**'], 'checks': ['unit'], 'reason': 'Contrato puro y sus pruebas.'}
        ]

    def plan(self, changes):
        return self.c.build_plan(self.root, self.p, changes, 'sha-example', ['CA01'])

    def receipt(self, plan):
        return {
            'schema_version': '1.0', 'plan_id': plan['plan_id'], 'candidate_digest': plan['candidate_digest'],
            'records': [{
                'check_id': 'unit', 'input_digest': plan['selected'][0]['input_digest'],
                'status': 'passed', 'exit_code': 0, 'collected': 2, 'executed': 2,
                'failed': 0, 'skipped': 0, 'assertions': {'CA01': 'passed'},
                'evidence': [{'path': 'receipt.json', 'sha256': self.evidence_hash}],
                'started_at': '2026-10-21T12:00:00Z', 'finished_at': '2026-10-21T12:00:01Z',
                'environment_id': 'local-python-example', 'authorization_ref': None,
                'reason': 'Salida estructurada de la suite.'
            }]
        }

    def prepare_receipt(self, plan):
        (self.root / 'receipt.json').write_text('{"executed":2}', encoding='utf-8')
        self.evidence_hash = self.c.file_hash(self.root / 'receipt.json')
        return self.receipt(plan)

    def test_unknown_file_blocks_instead_of_model_guess(self):
        plan = self.plan([{'status': 'M', 'path': 'src/unknown.py', 'old_path': None}])
        self.assertEqual('blocked', plan['status'])
        self.assertIn('UNCLASSIFIED_PATH', str(plan['blockers']))

    def test_same_inputs_make_same_plan(self):
        changes = [{'status': 'M', 'path': 'src/pure.py', 'old_path': None}]
        self.assertEqual(self.plan(changes), self.plan(changes))

    def test_fixture_change_invalidates_digest(self):
        changes = [{'status': 'M', 'path': 'src/pure.py', 'old_path': None}]
        before = self.plan(changes)
        (self.root / 'tests/fixtures/input.json').write_text('{"changed":true}', encoding='utf-8')
        after = self.plan(changes)
        self.assertNotEqual(before['selected'][0]['input_digest'], after['selected'][0]['input_digest'])

    def test_rename_checks_old_and_new_routes(self):
        plan = self.plan([{'status': 'R', 'path': 'src/unknown.py', 'old_path': 'src/pure.py'}])
        self.assertEqual('blocked', plan['status'])
        self.assertEqual(['unit'], [x['check_id'] for x in plan['selected']])

    def test_zero_tests_cannot_pass(self):
        plan = self.plan([{'status': 'M', 'path': 'src/pure.py', 'old_path': None}])
        receipt = self.prepare_receipt(plan)
        receipt['records'][0].update(collected=0, executed=0)
        self.assertEqual('blocked', self.c.evaluate(self.root, self.p, plan, receipt)['status'])

    def test_missing_assertion_blocks(self):
        plan = self.plan([{'status': 'M', 'path': 'src/pure.py', 'old_path': None}])
        receipt = self.prepare_receipt(plan)
        receipt['records'][0]['assertions'] = {}
        self.assertEqual('blocked', self.c.evaluate(self.root, self.p, plan, receipt)['status'])

    def test_valid_receipt_passes_and_stale_fixture_does_not(self):
        plan = self.plan([{'status': 'M', 'path': 'src/pure.py', 'old_path': None}])
        receipt = self.prepare_receipt(plan)
        self.assertEqual('passed', self.c.evaluate(self.root, self.p, plan, receipt)['status'])
        (self.root / 'tests/fixtures/input.json').write_text('{"new":1}', encoding='utf-8')
        self.assertEqual('blocked', self.c.evaluate(self.root, self.p, plan, receipt)['status'])

    def test_remote_pass_without_authorization_is_blocked(self):
        self.p['checks'][0].update(environment='databricks', effect='synthetic_write')
        plan = self.plan([{'status': 'M', 'path': 'src/pure.py', 'old_path': None}])
        receipt = self.prepare_receipt(plan)
        self.assertEqual('blocked', self.c.evaluate(self.root, self.p, plan, receipt)['status'])

    def test_evidence_tampering_is_detected(self):
        plan = self.plan([{'status': 'M', 'path': 'src/pure.py', 'old_path': None}])
        receipt = self.prepare_receipt(plan)
        (self.root / 'receipt.json').write_text('changed', encoding='utf-8')
        self.assertEqual('blocked', self.c.evaluate(self.root, self.p, plan, receipt)['status'])

    def test_traversal_is_rejected(self):
        with self.assertRaises(ValueError):
            self.c.safe_path(self.root, '../outside')

    def test_empty_unconfigured_catalog_blocks(self):
        self.p['setup_complete'] = False
        self.assertEqual('blocked', self.plan([])['status'])

    def test_required_criterion_without_check_blocks(self):
        plan = self.c.build_plan(self.root, self.p, [{'status':'M','path':'README.md','old_path':None}], 'x', ['CA02'])
        self.assertEqual('blocked', plan['status'])

    def test_failed_required_result_blocks(self):
        plan = self.plan([{'status':'M','path':'src/pure.py','old_path':None}])
        receipt = self.prepare_receipt(plan)
        receipt['records'][0].update(status='failed', exit_code=1, failed=1)
        self.assertEqual('blocked', self.c.evaluate(self.root, self.p, plan, receipt)['status'])

    def test_duplicate_check_id_rejected(self):
        self.p['checks'].append(copy.deepcopy(self.p['checks'][0]))
        with self.assertRaises(ValueError):
            self.c.validate_policy(self.p)

    def test_source_deleted_in_snapshot_is_recorded(self):
        (self.root / 'src/pure.py').unlink()
        plan = self.plan([{'status':'D','path':'src/pure.py','old_path':None}])
        self.assertIn('src/pure.py', plan['selected'][0]['snapshot']['missing'])

    def test_skipped_items_in_required_suite_block(self):
        plan = self.plan([{'status':'M','path':'src/pure.py','old_path':None}])
        receipt = self.prepare_receipt(plan)
        receipt['records'][0].update(collected=3, executed=2, skipped=1)
        self.assertEqual('blocked', self.c.evaluate(self.root, self.p, plan, receipt)['status'])

    def test_reuse_obeys_ttl_and_environment(self):
        check = self.p['checks'][0]
        prior = {'status':'passed','input_digest':'abc','environment_id':'env1',
                 'finished_at':'2026-10-21T12:00:00Z'}
        now = datetime(2026,10,21,12,30,tzinfo=timezone.utc)
        self.assertTrue(self.c.can_reuse(check,prior,'abc','env1',now))
        self.assertFalse(self.c.can_reuse(check,prior,'abc','env2',now))
        self.assertFalse(self.c.can_reuse(check,prior,'changed','env1',now))
        self.assertFalse(self.c.can_reuse(check,prior,'abc','env1',datetime(2026,10,21,14,tzinfo=timezone.utc)))

    def test_disabled_and_future_reuse_rejected(self):
        check = self.p['checks'][0]
        prior = {'status':'passed','input_digest':'abc','environment_id':'env1',
                 'finished_at':'2026-10-21T12:00:00Z'}
        check['reuse_seconds'] = 0
        self.assertFalse(self.c.can_reuse(check,prior,'abc','env1',datetime(2026,10,21,12,tzinfo=timezone.utc)))
        check['reuse_seconds'] = 100
        self.assertFalse(self.c.can_reuse(check,prior,'abc','env1',datetime(2026,10,21,11,tzinfo=timezone.utc)))

    def test_missing_result_blocks(self):
        plan = self.plan([{'status':'M','path':'src/pure.py','old_path':None}])
        receipt = self.prepare_receipt(plan)
        receipt['records'] = []
        self.assertEqual('blocked', self.c.evaluate(self.root, self.p, plan, receipt)['status'])

    def test_policy_change_invalidates_plan(self):
        plan = self.plan([{'status':'M','path':'src/pure.py','old_path':None}])
        receipt = self.prepare_receipt(plan)
        self.p['version'] = 'next'
        self.assertEqual('blocked', self.c.evaluate(self.root, self.p, plan, receipt)['status'])

    def test_boolean_exit_code_does_not_pass(self):
        plan = self.plan([{'status':'M','path':'src/pure.py','old_path':None}])
        receipt = self.prepare_receipt(plan)
        receipt['records'][0]['exit_code'] = False
        self.assertEqual('blocked', self.c.evaluate(self.root, self.p, plan, receipt)['status'])

    def test_no_required_assertions_is_invalid_policy(self):
        self.p['checks'][0]['required_assertions'] = []
        with self.assertRaises(ValueError):
            self.c.validate_policy(self.p)

    def test_nested_glob_snapshot_matches_selection_semantics(self):
        (self.root/'src/nested').mkdir()
        helper = self.root/'src/nested/helper.py'
        helper.write_text('value=1',encoding='utf-8')
        self.p['checks'][0]['inputs'] = ['src/*.py','tests/test_pure.py']
        self.p['rules'][1]['paths'] = ['src/*.py','tests/**']
        changes = [{'status':'M','path':'src/nested/helper.py','old_path':None}]
        first = self.plan(changes)
        helper.write_text('value=2',encoding='utf-8')
        second = self.plan(changes)
        self.assertNotEqual(first['selected'][0]['input_digest'],second['selected'][0]['input_digest'])

    def test_local_process_with_remote_effect_requires_authorization_ref(self):
        self.p['checks'][0]['effect'] = 'remote_read'
        plan = self.plan([{'status':'M','path':'src/pure.py','old_path':None}])
        receipt = self.prepare_receipt(plan)
        self.assertEqual('blocked',self.c.evaluate(self.root,self.p,plan,receipt)['status'])


if __name__ == '__main__':
    unittest.main()
