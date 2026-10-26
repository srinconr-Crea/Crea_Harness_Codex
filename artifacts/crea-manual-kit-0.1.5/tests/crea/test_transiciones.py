"""Contratos y consumidor: evidencia sintética, sin efectos remotos."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import test_testing_adapters as legacy
from testing import schemas, git_adapter
from testing.common import KIT, read, file_hash, digest
try:
    import transiciones as transitions
except ImportError:
    transitions = None


def handoff():
    return {'schema_version': '1.0',
            'identity': {'hu_id': 'local-synthetic', 'external_story_id': None, 'change': 'synthetic',
                         'phase': 'planificacion', 'attempt': 1, 'sender': 'planner', 'recipient': 'principal',
                         'agent_id': None, 'created_at': '2026-10-26T12:00:00Z'},
            'result': {'status': 'ready', 'completed': ['Criterios y plan preparados']},
            'scope': {'objective': 'Aclarar una guía', 'criteria': [{'path': 'criteria.md'}],
                      'approved_paths': ['docs/guide.md'], 'read_paths': ['criteria.md'],
                      'write_paths': ['docs/hu/synthetic/handoffs/planificacion-1.json'],
                      'actions': [], 'candidate_digest': None, 'base': None, 'head': None,
                      'entry': None, 'exit': None, 'moves': [], 'sync': [], 'git_inputs': {}},
            'context': {'layers': [], 'capabilities': [], 'not_applicable_reason': 'HU documental sin datos',
                        'rules': [], 'functional_decisions': [],
                        'risk': {'level': 'low', 'reason': 'Solo aclaración documental'}},
            'evidence': {'artifacts': [], 'decisions': [], 'objects': [],
                         'validation_plan': {'path': 'validation.md'}, 'tests': None, 'delivery': None},
            'pending': {'blockers': [], 'warnings': [], 'questions': [], 'exceptions': []},
            'continuation': {'transition': 'to_apply', 'next_step': 'Esperar nueva solicitud de Apply',
                             'authorization': None, 'decision_required': None}, 'previous_handoff': None}


class TransitionTests(unittest.TestCase):
    setUp = legacy.AdaptersTests.setUp
    cleanup = legacy.AdaptersTests.cleanup
    write = legacy.AdaptersTests.write
    git = legacy.AdaptersTests.git
    init_git = legacy.AdaptersTests.init_git

    def setup_handoff(self):
        self.init_git()
        self.write('criteria.md', 'CA01: instrucciones claras\n')
        self.write('validation.md', 'Revisar enlaces y pasos\n')
        config = read(KIT / 'docs/proyecto.json')
        config['project']['setup_complete'] = True
        self.write('docs/proyecto.json', json.dumps(config))
        h = handoff()
        name = 'docs/hu/synthetic/handoffs/planificacion-1.json'
        self.write(name, json.dumps(h))
        return h, name

    def test_planning_schema_does_not_require_future_test_results(self):
        schema = read(KIT / 'docs/plantillas/handoff.schema.json')
        schemas.validate_schema(schema, handoff())
        invalid = handoff()
        invalid['identity']['attempt'] = 0
        with self.assertRaises(ValueError):
            schemas.validate_schema(schema, invalid)
        invalid = handoff()
        invalid['context']['not_applicable_reason'] = ''
        with self.assertRaises(ValueError):
            schemas.validate_schema(schema, invalid)

    def test_project_extensions_are_optional_and_conditions_are_closed(self):
        config = read(KIT / 'docs/proyecto.json')
        config.pop('rules', None)
        config['workflow'].pop('transitions', None)
        schemas.validate('project', config)
        config['workflow']['transitions'] = {'mode': 'enforcing', 'blocking_conditions': ['GUESS']}
        with self.assertRaises(ValueError):
            schemas.validate('project', config)

    def test_consumer_error_informative_is_not_a_new_veto_or_pass(self):
        self.assertIsNotNone(transitions, 'Transition consumer not implemented')
        for report in (None, {'check_status': 'validator_error', 'new_control_effect': 'undetermined', 'findings': []}):
            decision = transitions.consume(report, 4, 'informative', [])
            self.assertTrue(decision['can_continue'])
            self.assertEqual(decision['validation'], 'undetermined')
        decision = transitions.consume(None, 4, 'informative', ['APPLY_AUTHORIZATION_MISSING'])
        self.assertFalse(decision['can_continue'])
        self.assertIsNone(transitions.consume(None, 4, 'informative', None)['can_continue'])

    def test_pending_decision_stops_only_dependent_continuation_and_can_resume(self):
        self.assertIsNotNone(transitions)
        waiting = transitions.consume({'check_status': 'completed', 'new_control_effect': 'report_only',
                                       'findings': [{'class': 'human_decision_pending'}]}, 3, 'informative', [])
        self.assertFalse(waiting['can_continue'])
        ready = transitions.consume({'check_status': 'completed', 'new_control_effect': 'allow', 'findings': []},
                                    0, 'informative', [])
        self.assertTrue(ready['can_continue'])

    def test_missing_approval_preserves_existing_stop_in_informative(self):
        self.assertIsNotNone(transitions)
        _, name = self.setup_handoff()
        report = transitions.check(self.root, name, 'to_apply')
        self.assertIn('APPLY_AUTHORIZATION_MISSING', report['existing_constraints'])
        self.assertFalse(transitions.consume(report, report['exit_code'], 'informative', report['existing_constraints'])['can_continue'])

    def test_authorized_planning_can_advance_without_test_results(self):
        self.assertIsNotNone(transitions)
        h, name = self.setup_handoff()
        self.write('approval.txt', 'Solicitud humana nueva: aplicar synthetic\n')
        h['continuation']['authorization'] = {'actions': ['apply'], 'response_ref': {'path': 'approval.txt'},
                                             'context_digest': digest(git_adapter.handoff_context(h)),
                                             'candidate_digest': None, 'delivery_digest': None}
        self.write(name, json.dumps(h))
        report = transitions.check(self.root, name, 'to_apply')
        self.assertEqual(report['existing_constraints'], [])
        self.assertEqual(report['check_status'], 'completed')

    def test_rules_select_only_declared_layer_and_capability_and_detect_missing(self):
        self.assertIsNotNone(transitions)
        config = read(KIT / 'docs/proyecto.json')
        config['rules'] = {'enabled': True, 'index_path': 'rules/README.md', 'common': ['rules/common.md'],
                           'layers': {'silver': 'rules/silver.md', 'gold': 'rules/gold.md'},
                           'capabilities': {'spark': 'rules/spark.md', 'sql': 'rules/sql.md'}}
        self.write('rules/README.md', 'Catálogo\n')
        for name, rule in [('common', 'COM-001'), ('silver', 'SIL-001'), ('spark', 'SPK-001')]:
            self.write('rules/' + name + '.md', 'Estado: active\nRevisión: 1\n### ' + rule + '\nComprobación: review\n')
        selected = transitions.select_rules(self.root, config, ['silver'], ['spark'], None)
        self.assertEqual([x['id'] for x in selected], ['COM-001', 'SIL-001', 'SPK-001'])
        with self.assertRaises(ValueError):
            transitions.select_rules(self.root, config, ['gold'], ['spark'], None)

    def test_schema_rejects_test_handoff_without_results(self):
        h = handoff()
        h['identity']['phase'] = 'pruebas'
        h['identity']['sender'] = 'tester'
        h['continuation']['transition'] = 'to_review'
        with self.assertRaises(ValueError):
            schemas.validate_schema(read(KIT / 'docs/plantillas/handoff.schema.json'), h)

    def test_render_has_one_source_and_exclusive_write_preserves_attempts(self):
        self.assertIsNotNone(transitions)
        h, name = self.setup_handoff()
        text = transitions.render(self.root, name)
        self.assertIn('derived_from: ' + name, text)
        self.assertIn('Decisión requerida:', text)
        output = 'docs/hu/synthetic/resumen.md'
        transitions.save(self.root, output, text, 'synthetic')
        with self.assertRaises(ValueError):
            transitions.save(self.root, output, 'overwrite', 'synthetic')
        with self.assertRaises(ValueError):
            transitions.save(self.root, '../outside.md', text, 'synthetic')

    def test_object_schema_does_not_allow_deployment_without_evidence(self):
        h = handoff()
        h['evidence']['objects'] = [{'object_id': 'guide', 'type': 'documentation', 'name': 'Guía',
           'layers': [], 'capabilities': [], 'not_applicable_reason': 'Documental',
           'operation': 'update', 'paths': ['docs/guide.md'], 'criteria': ['CA01'], 'rules': [],
           'planned': True, 'implementation': {'status': 'implemented', 'references': [{'path': 'docs/guide.md'}]},
           'deployment': {'status': 'evidenced', 'references': []},
           'verification': {'target': 'code', 'status': 'not_run', 'references': []}}]
        with self.assertRaises(ValueError):
            schemas.validate_schema(read(KIT / 'docs/plantillas/handoff.schema.json'), h)

    def test_pr_content_unicode_and_authority_are_provider_neutral(self):
        self.assertIsNotNone(transitions)
        content = {'title': 'Aclarar guía ñ & "pasos"', 'body': 'Problema\n\n- Cambio & evidencia\n',
                   'repository': 'https://github.com/example/sample', 'source_branch': 'feature/guía',
                   'target_branch': 'main', 'head_sha': 'a' * 40}
        from urllib.parse import urlparse, parse_qs
        values = parse_qs(urlparse(transitions.github_form(content)).query)
        self.assertEqual(values['title'][0], content['title'])
        self.assertEqual(values['body'][0], content['body'])
        self.assertTrue(transitions.verify_pr(content, {**content, 'id': '1', 'url': 'https://example.invalid/pr/1', 'state': 'active'}))
        self.assertFalse(transitions.verify_pr(content, {**content, 'title': 'changed', 'id': '1', 'url': 'https://example.invalid/pr/1', 'state': 'active'}))

    def test_existing_gate_failure_still_stops_informative_without_running_tests(self):
        h, name = self.setup_handoff()
        h['identity'].update({'phase': 'revision', 'sender': 'reviewer'})
        h['continuation']['transition'] = 'to_sync'
        h['evidence']['tests'] = {'plan': {'path': 'missing-plan.json'}, 'results': {'path': 'missing-results.json'}}
        name = name.replace('planificacion', 'revision')
        self.write(name, json.dumps(h))
        with patch.object(transitions.workflow, 'run', side_effect=AssertionError('transition ran tests')):
            report = transitions.check(self.root, name, 'to_sync')
        self.assertIn('REQUIRED_GATE_NOT_SATISFIED', report['existing_constraints'])
        self.assertFalse(transitions.consume(report, report['exit_code'], 'informative', report['existing_constraints'])['can_continue'])

    def test_role_write_scope_and_enabled_condition_block_only_requested_transition(self):
        h, name = self.setup_handoff()
        entry = git_adapter.observe(self.root)
        snapshot = 'docs/hu/synthetic/handoffs/planificacion-1-entrada.json'
        self.write(snapshot, json.dumps(entry))
        h['scope']['entry'] = {'path': snapshot}
        h['scope']['write_paths'].append(snapshot)
        self.write(name, json.dumps(h))
        self.write('mixed.txt', 'unexpected writer during interval\n')
        report = transitions.check(self.root, name, 'to_apply')
        self.assertEqual(report['new_control_effect'], 'report_only')
        self.assertTrue(any(x['condition_id'] == 'WRITE_SCOPE' and 'mixed.txt' in x['observed'] for x in report['findings']))
        config = read(self.root / 'docs/proyecto.json')
        self.write('promotion.txt', 'Responsable: habilitar WRITE_SCOPE tras casos revisados\n')
        config['workflow']['transitions'] = {'mode': 'enforcing', 'blocking_conditions': ['WRITE_SCOPE'], 'promotion_ref': 'promotion.txt'}
        self.write('docs/proyecto.json', json.dumps(config))
        report = transitions.check(self.root, name, 'to_apply')
        self.assertEqual(report['new_control_effect'], 'block')

    def test_invalid_contract_is_advisory_when_existing_approval_remains_valid(self):
        h, name = self.setup_handoff()
        self.write('approval.txt', 'Apply autorizado\n')
        h['continuation']['authorization'] = {'actions': ['apply'], 'response_ref': {'path': 'approval.txt'},
            'context_digest': digest(git_adapter.handoff_context(h)), 'candidate_digest': None, 'delivery_digest': None}
        del h['identity']['created_at']
        self.write(name, json.dumps(h))
        report = transitions.check(self.root, name, 'to_apply')
        self.assertEqual(report['exit_code'], 0)
        self.assertEqual(report['new_control_effect'], 'report_only')
        self.assertEqual(report['existing_constraints'], [])

    def test_dependency_error_cli_has_structured_code_four(self):
        import subprocess
        # Force an interpreter without site packages; no installation or global change.
        result = subprocess.run([sys.executable, '-S', '-B', str(KIT/'scripts/crea/transiciones.py'),
            'check', '--repo', str(self.root), '--handoff', 'none.json', '--transition', 'to_apply'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 4)
        self.assertEqual(json.loads(result.stdout)['check_status'], 'validator_error')

    def test_recording_resulting_commit_does_not_invalidate_approved_pr_content(self):
        packet = {'title': 'Aclaración', 'body': 'Comportamiento y evidencia', 'repository': 'sample',
                  'source_branch': 'feature/sample', 'target_branch': 'main', 'head_sha': 'a' * 40}
        before = transitions.delivery_digest(packet)
        packet['head_sha'] = 'b' * 40
        self.assertEqual(before, transitions.delivery_digest(packet))
        packet['title'] = 'Otro contenido'
        self.assertNotEqual(before, transitions.delivery_digest(packet))

    def test_validator_error_only_enforces_explicitly_required_new_conditions(self):
        self.assertTrue(transitions.consume(None, 4, 'enforcing', [], [])['can_continue'])
        self.assertFalse(transitions.consume(None, 4, 'enforcing', [], ['WRITE_SCOPE'])['can_continue'])

    def test_archive_reference_uses_only_exact_hash_bound_movement(self):
        self.init_git()
        source = 'openspec/changes/synthetic/proposal.md'
        target = 'openspec/changes/archive/2026-10-26-synthetic/proposal.md'
        path = self.write(target, 'approved artifact\n')
        movement = {'from': source, 'to': target, 'sha256': file_hash(path)}
        self.assertEqual(transitions.reference(self.root, {'path': source}, [movement]), path)
        self.write(target, 'different artifact\n')
        with self.assertRaises(ValueError):
            transitions.reference(self.root, {'path': source}, [movement])

    def test_later_writer_is_not_attributed_to_the_closed_role_interval(self):
        h, name = self.setup_handoff()
        entry = git_adapter.observe(self.root)
        entry_path = 'docs/hu/synthetic/handoffs/planificacion-1-entrada.json'
        exit_path = 'docs/hu/synthetic/handoffs/planificacion-1-salida.json'
        self.write(entry_path, json.dumps(entry))
        self.write('docs/guide.md', 'planner assigned document\n')
        exit_state = git_adapter.observe(self.root)
        self.write(exit_path, json.dumps(exit_state))
        h['scope']['entry'] = {'path': entry_path, 'sha256': file_hash(self.root/entry_path)}
        h['scope']['exit'] = {'path': exit_path, 'sha256': file_hash(self.root/exit_path)}
        h['scope']['write_paths'] += ['docs/guide.md', entry_path, exit_path]
        self.write(name, json.dumps(h))
        self.write('later-principal-note.md', 'later authorized writer\n')
        report = transitions.check(self.root, name, 'to_apply')
        related = [f for f in report['findings'] if 'later-principal-note.md' in f['observed']]
        self.assertTrue(related)
        self.assertTrue(all(f['owner'] == 'principal' and f['class'] == 'warning' for f in related))

    def test_second_attempt_requires_the_hash_of_its_real_predecessor(self):
        h, name = self.setup_handoff()
        h['identity']['attempt'] = 2
        next_path = name.replace('-1.json', '-2.json')
        self.write(next_path, json.dumps(h))
        with self.assertRaises(ValueError):
            transitions.validate_handoff(self.root, next_path)

    def test_publication_requires_a_distinct_pre_push_check(self):
        _, name = self.setup_handoff()
        report = transitions.check(self.root, name, 'to_publish')
        self.assertIn('PUBLICATION_OPERATION_REQUIRED', report['existing_constraints'])

    def test_pre_push_rejects_an_untested_commit_even_with_a_valid_current_gate(self):
        from testing import workflow
        base, policy_path, execution_path, outputs = legacy.AdaptersTests.local_setup(self)
        for name in ('criteria.md', 'validation.md', 'review.md', 'verify.md'):
            self.write(name, 'Synthetic reviewed evidence\n')
        self.write('approval.txt', 'Synthetic authorization: push candidate to the presented branch\n')
        policy = read(policy_path)
        policy['rules'].append({'id': 'DOCS', 'paths': ['*.md'], 'checks': [], 'reason': 'Synthetic reviewed documents'})
        self.write('policy.json', json.dumps(policy))
        execution = read(execution_path)
        execution['reviewed_policy_digest'] = digest(policy)
        self.write('execution.json', json.dumps(execution))
        config = read(KIT / 'docs/proyecto.json')
        config['project']['setup_complete'] = True
        config['validation']['testing'].update({'policy_path': 'policy.json', 'execution_path': 'execution.json'})
        self.write('docs/proyecto.json', json.dumps(config))
        h = handoff()
        h['scope']['git_inputs'] = {'unit': []}
        h['scope']['approved_paths'] = ['src/codes.py', 'tests/test_codes.py', 'pytest.ini', 'policy.json',
            'execution.json', 'docs/proyecto.json', 'criteria.md', 'validation.md', 'review.md', 'verify.md', 'approval.txt']
        self.write('docs/hu/synthetic/handoffs/planificacion-1.json', json.dumps(h))
        plan = workflow.make_plan(self.root, policy_path, execution_path, base, ['CA01'])
        results = workflow.run(self.root, policy_path, execution_path, plan)
        self.assertEqual(results['records'][0]['status'], 'passed')
        self.write(outputs[0], json.dumps(plan)); self.write(outputs[2], json.dumps(results))
        h['identity'].update({'phase': 'entrega', 'sender': 'principal'})
        h['scope']['candidate_digest'] = plan['candidate_digest']
        h['scope']['actions'] = ['push']
        h['evidence']['tests'] = {'plan': {'path': outputs[0]}, 'results': {'path': outputs[2]}}
        h['evidence']['artifacts'] = [{'path': 'review.md', 'kind': 'review'}, {'path': 'verify.md', 'kind': 'verify'}]
        h['evidence']['delivery'] = {'title': 'Synthetic candidate', 'body': 'Tested local behavior',
            'repository': 'sample', 'source_branch': 'feature/sample', 'target_branch': 'main',
            'head_sha': self.git('rev-parse', 'HEAD'), 'status': 'draft'}
        h['continuation']['transition'] = 'to_publish'
        h['continuation']['authorization'] = {'actions': ['push'], 'response_ref': {'path': 'approval.txt'},
            'context_digest': digest(git_adapter.handoff_context(h)), 'candidate_digest': plan['candidate_digest'],
            'delivery_digest': transitions.delivery_digest(h['evidence']['delivery'])}
        name = 'docs/hu/synthetic/handoffs/entrega-1.json'
        self.write(name, json.dumps(h))
        with patch.object(workflow.execution, 'run_process', side_effect=AssertionError('pre-push ran tests')):
            report = transitions.check(self.root, name, 'to_publish', operation='push')
        self.assertNotIn('REQUIRED_GATE_NOT_SATISFIED', report['existing_constraints'])
        self.assertIn('COMMIT_NOT_EQUIVALENT_BEFORE_PUSH', report['existing_constraints'])


if __name__ == '__main__':
    unittest.main()
