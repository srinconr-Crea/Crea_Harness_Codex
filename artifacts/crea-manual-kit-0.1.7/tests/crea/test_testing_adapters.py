"""Fixtures sintéticos: Git y procesos reales, sin red ni recursos remotos."""
import copy
import importlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import unittest
import uuid

KIT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KIT / 'scripts/crea'))
try:
    from testing import git_adapter, reports, schemas, execution, workflow
except ImportError:
    git_adapter = reports = schemas = execution = workflow = None


class AdaptersTests(unittest.TestCase):
    def setUp(self):
        self.scratch = KIT / '.test-work'
        self.root = self.scratch / uuid.uuid4().hex
        self.root.mkdir(parents=True)
        self.addCleanup(self.cleanup)

    def cleanup(self):
        target = self.root.resolve()
        if target.parent != self.scratch.resolve():
            raise ValueError('Unsafe fixture cleanup')
        def writable_retry(func, name, exc):
            p = Path(name).resolve()
            if not p.is_relative_to(target):
                raise ValueError('Cleanup escaped fixture')
            p.chmod(stat.S_IWRITE | stat.S_IREAD)
            func(name)
        shutil.rmtree(target, onexc=writable_retry)

    def write(self, path, text):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')
        return p

    def git(self, *args, ok=True):
        r = subprocess.run(['git', '-c', 'core.autocrlf=false', *args], cwd=self.root,
                           capture_output=True, text=True)
        if ok and r.returncode:
            self.fail(r.stderr)
        return r.stdout.strip()

    def init_git(self):
        self.git('init', '-b', 'fixture-base')
        self.git('config', 'user.name', 'Synthetic Tester')
        # An address is not required to exercise local Git identity.
        self.git('config', 'user.email', 'fixture.invalid')
        self.git('config', 'core.autocrlf', 'false')
        self.write('old name.txt', 'unchanged content for rename\n' * 5)
        self.write('deleted.txt', 'delete\n')
        self.write('mixed.txt', 'base\n')
        self.git('add', '--', 'old name.txt', 'deleted.txt', 'mixed.txt')
        self.git('commit', '-m', 'synthetic baseline')
        return self.git('rev-parse', 'HEAD')

    def test_git_inventory_includes_every_layer_and_rename_delete_untracked(self):
        self.assertIsNotNone(git_adapter, 'Git adapter not implemented')
        base = self.init_git()
        self.write('committed.txt', 'head\n')
        self.git('add', '--', 'committed.txt')
        self.git('commit', '-m', 'synthetic head')
        self.git('mv', 'old name.txt', 'new name.txt')
        self.git('rm', 'deleted.txt')
        self.write('mixed.txt', 'index\n')
        self.git('add', '--', 'mixed.txt')
        self.write('mixed.txt', 'worktree\n')
        self.write('new ü space.txt', 'untracked\n')
        receipt = git_adapter.collect(self.root, base, [])
        self.assertEqual(set(receipt['layers']), {'head', 'staged', 'unstaged', 'untracked', 'conflicts'})
        rows = {(x['status'], x['path'], x['old_path']) for x in receipt['changes']}
        self.assertIn(('R', 'new name.txt', 'old name.txt'), rows)
        self.assertIn(('D', 'deleted.txt', None), rows)
        self.assertIn(('A', 'new ü space.txt', None), rows)
        self.assertIn(('A', 'committed.txt', None), rows)
        self.assertEqual(receipt, git_adapter.collect(self.root, base, []))
        self.write('mixed.txt', 'changed again\n')
        self.assertNotEqual(receipt['input_digest'], git_adapter.collect(self.root, base, [])['input_digest'])

    def test_git_preserves_real_merge_conflicts(self):
        self.assertIsNotNone(git_adapter)
        base = self.init_git()
        self.git('checkout', '-b', 'fixture-side')
        self.write('mixed.txt', 'side\n')
        self.git('add', '--', 'mixed.txt')
        self.git('commit', '-m', 'side')
        self.git('checkout', 'fixture-base')
        self.write('mixed.txt', 'other\n')
        self.git('add', '--', 'mixed.txt')
        self.git('commit', '-m', 'other')
        self.git('merge', 'fixture-side', ok=False)
        r = git_adapter.collect(self.root, base, [])
        self.assertIn('mixed.txt', [x['path'] for x in r['changes'] if x['status'] == 'U'])

    def test_git_base_must_exist_and_be_ancestor(self):
        self.assertIsNotNone(git_adapter)
        self.init_git()
        with self.assertRaises(ValueError):
            git_adapter.collect(self.root, 'missing-base', [])
        self.git('checkout', '-b', 'fixture-future')
        self.write('mixed.txt', 'future\n')
        self.git('add', '--', 'mixed.txt')
        self.git('commit', '-m', 'future')
        future = self.git('rev-parse', 'HEAD')
        self.git('checkout', 'fixture-base')
        with self.assertRaises(ValueError):
            git_adapter.collect(self.root, future, [])

    def test_index_content_change_invalidates_with_identical_worktree(self):
        base = self.init_git()
        self.write('mixed.txt', 'index one\n')
        self.git('add', '--', 'mixed.txt')
        self.write('mixed.txt', 'same worktree\n')
        first = git_adapter.collect(self.root, base, [])
        self.write('mixed.txt', 'index two\n')
        self.git('add', '--', 'mixed.txt')
        self.write('mixed.txt', 'same worktree\n')
        self.assertNotEqual(first['input_digest'], git_adapter.collect(self.root, base, [])['input_digest'])

    def test_generated_evidence_exclusion_is_explicit_and_does_not_hide_code(self):
        self.assertIsNotNone(git_adapter)
        base = self.init_git()
        out = 'docs/hu/synthetic/pruebas/plan.json'
        self.write(out, '{}')
        first = git_adapter.collect(self.root, base, [out])
        self.write(out, '{"generated":true}')
        second = git_adapter.collect(self.root, base, [out])
        self.assertEqual(first['input_digest'], second['input_digest'])
        self.assertEqual(first['excluded'][0]['path'], out)
        self.assertNotEqual(first['excluded'], second['excluded'])
        for bad in ['mixed.txt', 'docs/hu/synthetic/pruebas/test_product.py', '../outside.json']:
            with self.assertRaises(ValueError):
                git_adapter.collect(self.root, base, [bad])

    def test_strict_schema_rejects_extra_fields_wrong_types_and_dates(self):
        self.assertIsNotNone(schemas)
        p = json.loads((KIT / '.agents/skills/Crea/crea-pruebas/assets/policy.template.json').read_text())
        schemas.validate('policy', p)
        p['setup_complete'] = 'true'
        with self.assertRaises(ValueError):
            schemas.validate('policy', p)
        p['setup_complete'] = False
        p['unexpected'] = True
        with self.assertRaises(ValueError):
            schemas.validate('policy', p)

    def test_strict_json_rejects_duplicate_keys_and_nonfinite_numbers(self):
        from testing.common import read
        for payload in ['{"key":1,"key":2}', '{"value":NaN}']:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                read(self.write('bad.json', payload))

    def test_schema_date_time_format_is_enforced(self):
        for timestamp in ['not-a-date', '2026-99-99T00:00:00Z']:
            with self.subTest(timestamp=timestamp), self.assertRaises(ValueError):
                schemas.validate_schema({'type': 'string', 'format': 'date-time'}, timestamp)

    def test_coverage_rejects_malformed_data_and_invalid_line_numbers(self):
        for data in [{'files': []}, {'files': {'src/codes.py': {'executed_lines': ['not-a-line'], 'missing_lines': []}}},
                     {'files': {'src/codes.py': {'executed_lines': [True, -1, 0], 'missing_lines': []}}}]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                reports.coverage(self.write('invalid-coverage.json', json.dumps(data)), ['src/codes.py'], 100)

    def test_junit_requires_real_cases_assertions_and_no_skips(self):
        self.assertIsNotNone(reports)
        path = self.write('report.xml', '<testsuites><testsuite tests="2" failures="0" errors="0" skipped="0"><testcase classname="test_codes" name="test_valid"/><testcase classname="test_codes" name="test_invalid"/></testsuite></testsuites>')
        r = reports.junit(path, {'CA01': ['test_codes::test_valid'], 'CA02': ['test_codes::test_invalid']})
        self.assertEqual((r['collected'], r['executed'], r['skipped']), (2, 2, 0))
        self.assertEqual(r['assertions'], {'CA01': 'passed', 'CA02': 'passed'})
        self.assertEqual(reports.junit(path, {'CA03': ['test_codes::absent']})['assertions']['CA03'], 'blocked')
        path.write_text('<testsuites><testsuite tests="0"/></testsuites>')
        with self.assertRaises(ValueError):
            reports.junit(path, {})
        path.write_text('<testsuite tests="1"><testcase classname="test_codes" name="test_valid"><skipped/></testcase></testsuite>')
        self.assertEqual(reports.junit(path, {'CA01': ['test_codes::test_valid']})['assertions']['CA01'], 'blocked')

    def test_junit_rejects_inconsistent_counters_duplicate_ids_and_entities(self):
        self.assertIsNotNone(reports)
        for content in ['<testsuite tests="9"><testcase name="one"/></testsuite>',
                        '<testsuite tests="2"><testcase name="same"/><testcase name="same"/></testsuite>',
                        '<!DOCTYPE x [<!ENTITY a "attack">]><testsuite tests="1"><testcase name="&a;"/></testsuite>']:
            with self.subTest(content=content), self.assertRaises(ValueError):
                reports.junit(self.write('bad.xml', content), {})

    def test_coverage_requires_target_files_and_executable_lines(self):
        self.assertIsNotNone(reports)
        path = self.write('coverage.json', json.dumps({'files': {'src/codes.py': {'executed_lines': [1, 2], 'missing_lines': [3]}}, 'totals': {'percent_covered': 99}}))
        self.assertFalse(reports.coverage(path, ['src/codes.py'], 80)['passed'])
        self.assertTrue(reports.coverage(path, ['src/codes.py'], 60)['passed'])
        with self.assertRaises(ValueError):
            reports.coverage(path, ['src/missing.py'], 60)

    def test_executor_uses_reviewed_argv_minimal_environment_and_redacted_bounded_logs(self):
        self.assertIsNotNone(execution)
        self.write('probe.py', 'import os; print(os.getenv("SYNTHETIC_SECRET", "absent")); print("token=synthetic-private"); print("x"*200000)')
        os.environ['SYNTHETIC_SECRET'] = 'must-not-inherit'
        self.addCleanup(os.environ.pop, 'SYNTHETIC_SECRET', None)
        r = execution.run_process(self.root, ['python', 'probe.py'], sys.executable, 5)
        self.assertEqual(r['exit_code'], 0)
        self.assertIn('absent', r['stdout'])
        self.assertNotIn('synthetic-private', r['stdout'])
        self.assertLessEqual(len(r['stdout'].encode()), 66000)
        self.assertTrue(r['stdout_truncated'])
        with self.assertRaises(ValueError):
            execution.run_process(self.root, ['cmd', '/c', 'anything'], sys.executable, 5)

    def test_executor_timeout_is_not_passed(self):
        self.assertIsNotNone(execution)
        self.write('slow.py', 'import time; time.sleep(5)')
        r = execution.run_process(self.root, ['python', 'slow.py'], sys.executable, 1)
        self.assertTrue(r['timed_out'])
        self.assertNotEqual(r['exit_code'], 0)

    def local_setup(self):
        base = self.init_git()
        self.write('src/codes.py', 'def code(value):\n    if not isinstance(value, str):\n        raise ValueError("type")\n    return value.strip()\n')
        self.write('tests/test_codes.py', 'from src.codes import code\nimport pytest\ndef test_valid():\n    assert code(" 0012 ") == "0012"\ndef test_invalid():\n    with pytest.raises(ValueError):\n        code(None)\n')
        self.write('pytest.ini', '[pytest]\n')
        prefix = 'docs/hu/synthetic/pruebas/'
        outputs = [prefix + x for x in ['plan.json', 'git.json', 'resultados.json', 'gate.json',
                   'junit-unit.xml', 'receipt-unit.json', 'stdout-unit.log', 'stderr-unit.log']]
        policy = {'schema_version': '1.0', 'policy_id': 'synthetic', 'version': '1', 'setup_complete': True,
                  'checks': [{'id': 'unit', 'kind': 'pytest', 'environment': 'local', 'effect': 'local_execution',
                              'argv': ['python', '-m', 'pytest', '-c', 'pytest.ini', '-q', '-p', 'no:cacheprovider', 'tests/test_codes.py',
                                       '--junitxml=' + prefix + 'junit-unit.xml'],
                              'configured': True, 'timeout_seconds': 20,
                              'inputs': ['src/codes.py', 'tests/test_codes.py', 'pytest.ini'], 'criteria': ['CA01', 'CA02'],
                              'required_assertions': ['CA01', 'CA02'], 'min_tests': 2, 'reuse_seconds': 0}],
                  'rules': [{'id': 'SYNTHETIC', 'paths': ['*.txt', 'src/*', 'tests/*', 'policy.json', 'execution.json', 'pytest.ini', 'docs/proyecto.json'],
                             'checks': ['unit'], 'reason': 'Synthetic local contract'}]}
        from testing.common import digest
        settings = {'schema_version': '1.0', 'python_executable': sys.executable,
                    'reviewed_policy_digest': digest(policy), 'max_evidence_age_seconds': 3600,
                    'outputs': outputs, 'checks': {'unit': {'junit_path': prefix + 'junit-unit.xml',
                    'assertion_tests': {'CA01': ['tests.test_codes::test_valid'], 'CA02': ['tests.test_codes::test_invalid']},
                    'coverage_path': None, 'coverage_files': [], 'coverage_minimum': None}}}
        p = self.write('policy.json', json.dumps(policy))
        e = self.write('execution.json', json.dumps(settings))
        return base, p, e, outputs

    def test_real_pytest_plan_run_gate_and_no_business_execution_during_plan(self):
        self.assertTrue(hasattr(workflow, 'make_plan'), 'Workflow adapter not implemented')
        base, p, e, outputs = self.local_setup()
        plan = workflow.make_plan(self.root, p, e, base, ['CA01', 'CA02'])
        self.assertEqual(plan['status'], 'ready')
        self.assertFalse((self.root / outputs[4]).exists())
        result = workflow.run(self.root, p, e, plan)
        receipt_path = self.root / 'docs/hu/synthetic/pruebas/receipt-unit.json'
        self.assertEqual(result['records'][0]['status'], 'passed', json.loads(receipt_path.read_text())['report'])
        self.assertEqual(workflow.gate(self.root, p, e, plan, result)['status'], 'passed')
        with self.assertRaises(ValueError):
            workflow.run(self.root, p, e, plan)
        self.write('src/codes.py', '# invalidated candidate\n')
        self.assertEqual(workflow.gate(self.root, p, e, plan, result)['status'], 'blocked')

    def test_argv_policy_review_and_runtime_requirements_fail_closed(self):
        self.assertTrue(hasattr(workflow, 'make_plan'))
        base, p, e, outputs = self.local_setup()
        policy = json.loads(p.read_text())
        policy['checks'][0]['environment'] = 'databricks'
        policy['checks'][0]['kind'] = 'runtime'
        p.write_text(json.dumps(policy))
        plan = workflow.make_plan(self.root, p, e, base, ['CA01'])
        result = workflow.run(self.root, p, e, plan)
        self.assertEqual(result['records'][0]['status'], 'blocked')
        self.assertEqual(workflow.gate(self.root, p, e, plan, result)['status'], 'blocked')
        self.assertFalse((self.root / outputs[4]).exists())

    def test_new_untracked_input_and_configuration_change_invalidate_plan(self):
        self.assertTrue(hasattr(workflow, 'make_plan'))
        base, p, e, _ = self.local_setup()
        plan = workflow.make_plan(self.root, p, e, base, ['CA01'])
        self.write('unclassified.bin', 'new input')
        with self.assertRaises(ValueError):
            workflow.run(self.root, p, e, plan)

    def test_modified_or_foreign_receipt_never_passes(self):
        self.assertTrue(hasattr(workflow, 'make_plan'))
        base, p, e, _ = self.local_setup()
        plan = workflow.make_plan(self.root, p, e, base, ['CA01'])
        result = workflow.run(self.root, p, e, plan)
        other = copy.deepcopy(result)
        other['plan_id'] = '0' * 64
        self.assertEqual(workflow.gate(self.root, p, e, plan, other)['status'], 'blocked')
        receipt = self.root / 'docs/hu/synthetic/pruebas/receipt-unit.json'
        receipt.write_text('{}')
        self.assertEqual(workflow.gate(self.root, p, e, plan, result)['status'], 'blocked')

    def test_required_check_reference_selects_catalog_without_duplicate_commands(self):
        from testing.common import contract, read
        _, p, _, _ = self.local_setup()
        policy = read(p)
        policy['rules'] = [{'id': 'DOC', 'paths': ['README.md'], 'checks': [], 'reason': 'Documentation'}]
        self.write('README.md', 'synthetic documentation')
        plan = contract.build_plan(self.root, policy, [{'path': 'README.md', 'status': 'M'}],
                                   'synthetic-base', [], required_check_ids=['unit'])
        self.assertEqual([x['check_id'] for x in plan['selected']], ['unit'])
        self.assertIn('fixed-required-check-reference', plan['selected'][0]['rule_ids'])

    def test_document_only_selection_does_not_select_spark_or_start_process(self):
        from testing.common import contract, read
        _, p, _, outputs = self.local_setup()
        policy = read(p)
        policy['rules'] = [{'id': 'DOC', 'paths': ['README.md'], 'checks': [], 'reason': 'Documentation'}]
        self.write('README.md', 'synthetic documentation')
        plan = contract.build_plan(self.root, policy, [{'path': 'README.md', 'status': 'M'}], 'synthetic-base', [])
        self.assertEqual(plan['selected'], [])
        self.assertFalse((self.root / outputs[4]).exists())

    def test_evidence_expiry_blocks_without_rerunning_suite(self):
        import time
        base, p, e, _ = self.local_setup()
        settings = json.loads(e.read_text())
        settings['max_evidence_age_seconds'] = 1
        e.write_text(json.dumps(settings))
        plan = workflow.make_plan(self.root, p, e, base, ['CA01'])
        result = workflow.run(self.root, p, e, plan)
        self.assertEqual(result['records'][0]['status'], 'passed')
        time.sleep(2)
        self.assertEqual(workflow.gate(self.root, p, e, plan, result)['status'], 'blocked')

    def test_cli_gate_cannot_overwrite_primary_results(self):
        from testing.common import read, write
        base, p, e, outputs = self.local_setup()
        project = read(KIT / 'docs/proyecto.json')
        project['project']['setup_complete'] = True
        project['validation']['testing']['policy_path'] = 'policy.json'
        project['validation']['testing']['execution_path'] = 'execution.json'
        write(self.root / 'docs/proyecto.json', project)
        plan = workflow.make_plan(self.root, p, e, base, ['CA01', 'CA02'])
        result = workflow.run(self.root, p, e, plan)
        self.assertEqual(result['records'][0]['status'], 'passed')
        write(self.root / outputs[0], plan)
        write(self.root / outputs[2], result)
        before = (self.root / outputs[2]).read_bytes()
        response = subprocess.run([sys.executable, '-B', str(KIT / 'scripts/crea/pruebas.py'), 'gate',
                  '--repo', str(self.root), '--policy', 'policy.json', '--execution', 'execution.json',
                  '--plan', outputs[0], '--results', outputs[2], '--out', outputs[2]], capture_output=True)
        self.assertEqual((self.root / outputs[2]).read_bytes(), before, response.stdout)
        self.assertEqual(response.returncode, 2)

    def test_cli_gate_rejects_hardlink_alias_of_primary_results(self):
        from testing.common import read, write
        base, p, e, outputs = self.local_setup()
        project = read(KIT / 'docs/proyecto.json')
        project['project']['setup_complete'] = True
        project['validation']['testing']['policy_path'] = 'policy.json'
        project['validation']['testing']['execution_path'] = 'execution.json'
        write(self.root / 'docs/proyecto.json', project)
        plan = workflow.make_plan(self.root, p, e, base, ['CA01', 'CA02'])
        result = workflow.run(self.root, p, e, plan)
        write(self.root / outputs[0], plan)
        write(self.root / outputs[2], result)
        before = (self.root / outputs[2]).read_bytes()
        os.link(self.root / outputs[2], self.root / outputs[3])
        response = subprocess.run([sys.executable, '-B', str(KIT / 'scripts/crea/pruebas.py'), 'gate',
                  '--repo', str(self.root), '--policy', 'policy.json', '--execution', 'execution.json',
                  '--plan', outputs[0], '--results', outputs[2], '--out', outputs[3]], capture_output=True)
        self.assertEqual((self.root / outputs[2]).read_bytes(), before, response.stdout)
        self.assertEqual(response.returncode, 2)

    def test_cli_malformed_execution_is_structured_block(self):
        from testing.common import read, write
        _, p, e, outputs = self.local_setup()
        project = read(KIT / 'docs/proyecto.json')
        project['project']['setup_complete'] = True
        project['validation']['testing']['policy_path'] = 'policy.json'
        project['validation']['testing']['execution_path'] = 'execution.json'
        write(self.root / 'docs/proyecto.json', project)
        config = read(e)
        config['checks'] = []
        write(e, config)
        response = subprocess.run([sys.executable, '-B', str(KIT / 'scripts/crea/pruebas.py'), 'gate',
                  '--repo', str(self.root), '--policy', 'policy.json', '--execution', 'execution.json',
                  '--plan', outputs[0], '--results', outputs[2], '--out', outputs[3]], capture_output=True)
        self.assertEqual(response.returncode, 2, response.stderr)
        self.assertEqual(json.loads(response.stderr)['status'], 'blocked')


if __name__ == '__main__':
    unittest.main()
