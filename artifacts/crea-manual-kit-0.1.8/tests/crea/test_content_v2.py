"""Identidad por contenido: Git real en repositorios sintéticos, sin red."""
import copy
import json
from pathlib import Path
import sys
import unittest

import test_testing_adapters as legacy
from testing import git_adapter, workflow
from testing.common import digest


class ContentTests(unittest.TestCase):
    setUp = legacy.AdaptersTests.setUp
    cleanup = legacy.AdaptersTests.cleanup
    write = legacy.AdaptersTests.write
    git = legacy.AdaptersTests.git
    init_git = legacy.AdaptersTests.init_git
    local_setup = legacy.AdaptersTests.local_setup

    def projection(self):
        return {'version': 'content-v2', 'change': 'synthetic', 'context': {},
                'moves': [], 'sync': [], 'git_inputs': {'unit': []}}

    def test_content_identity_survives_stage_commit_but_not_code_changes(self):
        base = self.init_git()
        self.write('src/a.py', 'value = 1\n')
        p = self.projection()
        first = git_adapter.content_view(self.root, base, [], p)
        self.git('add', '--', 'src/a.py')
        staged = git_adapter.content_view(self.root, base, [], p)
        self.git('commit', '-m', 'same content')
        committed = git_adapter.content_view(self.root, base, [], p)
        self.assertEqual(first['input_digest'], staged['input_digest'])
        self.assertEqual(first['input_digest'], committed['input_digest'])
        self.assertNotEqual(first['observation']['head_sha'], committed['observation']['head_sha'])
        self.write('src/a.py', 'value = 2\n')
        self.assertNotEqual(first['input_digest'], git_adapter.content_view(self.root, base, [], p)['input_digest'])

    def test_snapshot_distinguishes_previous_and_new_changes_in_same_file(self):
        self.init_git()
        self.write('mixed.txt', 'developer\n')
        entry = git_adapter.observe(self.root)
        self.write('docs/receipt.md', 'tester\n')
        self.assertEqual(git_adapter.scope_changes(entry, git_adapter.observe(self.root)), ['docs/receipt.md'])
        self.write('mixed.txt', 'tester changed production\n')
        self.assertEqual(git_adapter.scope_changes(entry, git_adapter.observe(self.root)), ['docs/receipt.md', 'mixed.txt'])

    def test_git_functional_inputs_invalidate_identical_files_and_unknown_is_unsupported(self):
        base = self.init_git()
        p = self.projection()
        p['git_inputs'] = {'unit': ['branch']}
        first = git_adapter.content_view(self.root, base, [], p)
        self.git('checkout', '-b', 'different-branch')
        self.assertNotEqual(first['input_digest'], git_adapter.content_view(self.root, base, [], p)['input_digest'])
        p['git_inputs'] = {'unit': ['unknown-state']}
        with self.assertRaisesRegex(ValueError, 'GIT_INPUT_NOT_SUPPORTED'):
            git_adapter.content_view(self.root, base, [], p)

    def test_exact_archive_movement_preserves_inputs_and_tamper_does_not(self):
        base = self.init_git()
        source = 'openspec/changes/synthetic/proposal.md'
        dest = 'openspec/changes/archive/2026-10-26-synthetic/proposal.md'
        self.write(source, 'approved proposal\n')
        from testing.common import file_hash
        p = self.projection()
        p['moves'] = [{'from': source, 'to': dest, 'sha256': file_hash(self.root / source)}]
        before = git_adapter.content_view(self.root, base, [], p)
        (self.root / dest).parent.mkdir(parents=True)
        (self.root / source).rename(self.root / dest)
        after = git_adapter.content_view(self.root, base, [], p)
        self.assertEqual(before['input_digest'], after['input_digest'])
        self.write(dest, 'unreviewed behavior\n')
        with self.assertRaisesRegex(ValueError, 'ARCHIVE_CONTENT_CHANGED'):
            git_adapter.content_view(self.root, base, [], p)

    def test_full_plan_run_gate_survives_commit_without_reexecuting(self):
        base, policy, execution, outputs = self.local_setup()
        p = self.projection()
        plan = workflow.make_plan(self.root, policy, execution, base, ['CA01'], projection=p)
        result = workflow.run(self.root, policy, execution, plan)
        self.assertEqual(result['records'][0]['status'], 'passed')
        self.git('add', '--', 'src', 'tests', 'policy.json', 'execution.json', 'pytest.ini')
        self.git('commit', '-m', 'tested content')
        from unittest.mock import patch
        with patch.object(workflow.execution, 'run_process', side_effect=AssertionError('gate executed suites')):
            self.assertEqual(workflow.gate(self.root, policy, execution, plan, result)['status'], 'passed')
        self.write('src/codes.py', 'def code(value): return "changed"\n')
        self.assertEqual(workflow.gate(self.root, policy, execution, plan, result)['status'], 'blocked')

    def test_partial_staging_is_not_equivalent_to_the_tested_tree(self):
        base = self.init_git()
        self.write('mixed.txt', 'staged old\n')
        self.git('add', '--', 'mixed.txt')
        self.write('mixed.txt', 'tested new\n')
        with self.assertRaisesRegex(ValueError, 'INDEX_DIFFERS_FROM_TESTED_CONTENT'):
            git_adapter.verify_index(self.root, ['mixed.txt'])

    def test_future_handoff_is_observed_without_editing_frozen_plan_policy(self):
        from test_transiciones import handoff
        base = self.init_git()
        h = handoff()
        p = self.projection()
        p['context'] = git_adapter.handoff_context(h)
        first = git_adapter.content_view(self.root, base, [], p)
        self.write('docs/hu/synthetic/handoffs/planificacion-1.json', json.dumps(h))
        second = git_adapter.content_view(self.root, base, [], p)
        self.assertEqual(first['input_digest'], second['input_digest'])
        self.assertTrue(second['excluded'])
        h['identity']['attempt'] = 2
        h['evidence']['artifacts'] = [{'path': 'existing-receipt.json'}]
        from testing.common import file_hash
        h['previous_handoff'] = {'path': 'docs/hu/synthetic/handoffs/planificacion-1.json',
                                'sha256': file_hash(self.root / 'docs/hu/synthetic/handoffs/planificacion-1.json')}
        self.write('docs/hu/synthetic/handoffs/planificacion-2.json', json.dumps(h))
        self.assertEqual(first['input_digest'], git_adapter.content_view(self.root, base, [], p)['input_digest'])
        h['scope']['objective'] = 'unapproved scope'
        self.write('docs/hu/synthetic/handoffs/planificacion-2.json', json.dumps(h))
        with self.assertRaisesRegex(ValueError, 'HANDOFF_CONTEXT_CHANGED'):
            git_adapter.content_view(self.root, base, [], p)

    def test_publication_rejects_foreign_commit_even_when_final_tree_is_equal(self):
        base = self.init_git()
        self.write('src/a.py', 'approved\n')
        self.git('add', '--', 'src/a.py')
        self.git('commit', '-m', 'approved change')
        view = git_adapter.content_view(self.root, base, [], self.projection())
        self.assertTrue(git_adapter.verify_commit(self.root, base, 'HEAD', view, ['src/a.py']))
        self.write('foreign.txt', 'not authorized\n')
        self.git('add', '--', 'foreign.txt')
        self.git('commit', '-m', 'foreign change')
        self.git('rm', 'foreign.txt')
        self.git('commit', '-m', 'remove foreign file')
        with self.assertRaisesRegex(ValueError, 'COMMIT_OUTSIDE_APPROVED_SCOPE'):
            git_adapter.verify_commit(self.root, base, 'HEAD', view, ['src/a.py'])

    def test_exact_sync_projection_and_changed_output_are_distinguished(self):
        base = self.init_git()
        self.write('openspec/changes/synthetic/specs/guide/spec.md', 'approved delta\n')
        p = self.projection()
        import hashlib
        target = 'openspec/specs/guide/spec.md'
        p['sync'] = [{'path': target, 'before_sha256': None,
                      'after_sha256': hashlib.sha256(b'approved stable spec\n').hexdigest(), 'before_entry': None}]
        first = git_adapter.content_view(self.root, base, [], p)
        self.write(target, '').write_bytes(b'approved stable spec\n')
        self.assertEqual(first['input_digest'], git_adapter.content_view(self.root, base, [], p)['input_digest'])
        self.write(target, 'unapproved behavior\n')
        with self.assertRaisesRegex(ValueError, 'SYNC_CONTENT_CHANGED'):
            git_adapter.content_view(self.root, base, [], p)

    def test_pr_text_views_do_not_invalidate_technical_content(self):
        from test_transiciones import handoff
        base = self.init_git()
        h = handoff()
        h['evidence']['delivery'] = {'title': 'Título revisado', 'body': 'Cuerpo revisado\n',
            'repository': 'sample', 'source_branch': 'feature/sample', 'target_branch': 'main',
            'head_sha': 'a' * 40, 'status': 'draft'}
        p = self.projection()
        p['context'] = git_adapter.handoff_context(h)
        self.write('docs/hu/synthetic/handoffs/planificacion-1.json', json.dumps(h))
        before = git_adapter.content_view(self.root, base, [], p)
        self.write('docs/hu/synthetic/pr-title.txt', h['evidence']['delivery']['title'])
        self.write('docs/hu/synthetic/pr-body.md', h['evidence']['delivery']['body'])
        self.assertEqual(before['input_digest'], git_adapter.content_view(self.root, base, [], p)['input_digest'])
        self.write('docs/hu/synthetic/pr-body.md', 'unapproved title/body\n')
        self.assertNotEqual(before['input_digest'], git_adapter.content_view(self.root, base, [], p)['input_digest'])

    def test_previous_context_can_be_frozen_as_history_in_a_new_plan(self):
        from test_transiciones import handoff
        from testing.common import file_hash
        base = self.init_git()
        h = handoff()
        name = 'docs/hu/synthetic/handoffs/planificacion-1.json'
        path = self.write(name, json.dumps(h))
        p = self.projection()
        p['context'] = {**git_adapter.handoff_context(h), 'objective': 'New approved objective'}
        p['history'] = {name: file_hash(path)}
        before = git_adapter.content_view(self.root, base, [], p)
        h['result']['completed'] = ['changed historic record']
        self.write(name, json.dumps(h))
        with self.assertRaises(ValueError):
            git_adapter.content_view(self.root, base, [], p)

    def test_receipt_reference_correction_preserves_real_gate_without_rerunning(self):
        from test_transiciones import handoff
        from unittest.mock import patch
        base, policy, execution, _ = self.local_setup()
        self.write('criteria.md', 'CA01 and CA02 synthetic criteria\n')
        self.write('validation.md', 'Execute selected local unit check\n')
        catalog = json.loads(policy.read_text())
        catalog['rules'].append({'id': 'DOCS', 'paths': ['criteria.md', 'validation.md'], 'checks': [],
                                 'reason': 'Reviewed synthetic requirements'})
        policy.write_text(json.dumps(catalog))
        settings = json.loads(execution.read_text())
        settings['reviewed_policy_digest'] = digest(catalog)
        execution.write_text(json.dumps(settings))
        h = handoff()
        h['scope']['git_inputs'] = {'unit': []}
        self.write('docs/hu/synthetic/handoffs/planificacion-1.json', json.dumps(h))
        projection = self.projection()
        projection['context'] = git_adapter.handoff_context(h)
        plan = workflow.make_plan(self.root, policy, execution, base, ['CA01'], projection=projection)
        result = workflow.run(self.root, policy, execution, plan)
        self.assertEqual(result['records'][0]['status'], 'passed')
        h['identity']['attempt'] = 2
        h['previous_handoff'] = {'path': 'docs/hu/synthetic/handoffs/planificacion-1.json'}
        from testing.common import file_hash
        h['previous_handoff']['sha256'] = file_hash(self.root / h['previous_handoff']['path'])
        h['evidence']['artifacts'] = [{'path': 'docs/hu/synthetic/pruebas/receipt-unit.json', 'kind': 'receipt'}]
        self.write('docs/hu/synthetic/handoffs/planificacion-2.json', json.dumps(h))
        with patch.object(workflow.execution, 'run_process', side_effect=AssertionError('gate ran suites')):
            self.assertEqual(workflow.gate(self.root, policy, execution, plan, result)['status'], 'passed')

    def test_snapshot_reports_head_and_branch_actions_even_with_equal_files(self):
        self.init_git()
        entry = git_adapter.observe(self.root)
        self.git('checkout', '-b', 'different-actor-branch')
        self.git('commit', '--allow-empty', '-m', 'unassigned action')
        differences = git_adapter.scope_changes(entry, git_adapter.observe(self.root))
        self.assertIn('.git/HEAD', differences)
        self.assertIn('.git/branch', differences)

    def test_index_rejects_staged_files_outside_the_final_approval(self):
        self.init_git()
        self.write('foreign.txt', 'outside approval\n')
        self.git('add', '--', 'foreign.txt')
        with self.assertRaisesRegex(ValueError, 'STAGED_OUTSIDE_APPROVED_SCOPE'):
            git_adapter.verify_index(self.root, ['mixed.txt'])

    def test_published_derived_bytes_must_match_the_reviewed_worktree(self):
        from test_transiciones import handoff
        base = self.init_git()
        h = handoff()
        path = 'docs/hu/synthetic/handoffs/planificacion-1.json'
        self.write(path, json.dumps(h))
        self.git('add', '--', path)
        self.git('commit', '-m', 'old metadata')
        h['result']['completed'] = ['reviewed metadata differs from committed metadata']
        self.write(path, json.dumps(h))
        p = self.projection(); p['context'] = git_adapter.handoff_context(h)
        view = git_adapter.content_view(self.root, base, [], p)
        with self.assertRaisesRegex(ValueError, 'COMMIT_DIFFERS_FROM_REVIEWED_METADATA'):
            git_adapter.verify_commit(self.root, base, 'HEAD', view, [path])

    def test_initial_plan_freezes_same_context_handoff_bytes(self):
        from test_transiciones import handoff
        base, policy, execution, _ = self.local_setup()
        h = handoff()
        path = 'docs/hu/synthetic/handoffs/planificacion-1.json'
        self.write(path, json.dumps(h))
        p = self.projection(); p['context'] = git_adapter.handoff_context(h)
        plan = workflow.make_plan(self.root, policy, execution, base, ['CA01'], projection=p)
        h['result']['status'] = 'blocked'
        self.write(path, json.dumps(h))
        with self.assertRaisesRegex(ValueError, 'HISTORIC_HANDOFF_CHANGED'):
            workflow.current(self.root, policy, execution, plan)

    def test_declared_task_checkbox_progress_is_not_a_new_functional_candidate(self):
        from testing.common import file_hash
        base = self.init_git()
        source = 'openspec/changes/synthetic/tasks.md'
        target = 'openspec/changes/archive/2026-10-26-synthetic/tasks.md'
        payload = b'# Tasks\n\n- [ ] 1.1 Implement approved behavior\n'
        path = self.write(source, ''); path.write_bytes(payload)
        p = self.projection()
        p['moves'] = [{'from': source, 'to': target, 'sha256': file_hash(path), 'normalization': 'task_checkboxes'}]
        before = git_adapter.content_view(self.root, base, [], p)
        path.write_bytes(payload.replace(b'[ ]', b'[x]'))
        (self.root/target).parent.mkdir(parents=True)
        path.rename(self.root/target)
        self.assertEqual(before['input_digest'], git_adapter.content_view(self.root, base, [], p)['input_digest'])
        (self.root/target).write_bytes(payload.replace(b'approved', b'other'))
        with self.assertRaises(ValueError):
            git_adapter.content_view(self.root, base, [], p)


if __name__ == '__main__':
    unittest.main()
