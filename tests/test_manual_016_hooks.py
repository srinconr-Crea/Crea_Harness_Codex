import json
import os
import subprocess
from pathlib import Path
import sys
import contextlib
import shutil
import uuid
import unittest
from unittest.mock import patch

KIT = Path(__file__).resolve().parents[1] / 'artifacts/crea-manual-kit-0.1.6'
sys.path.insert(0, str(KIT / 'scripts/crea'))
@contextlib.contextmanager
def workspace_temp():
    root = KIT.parents[1] / '.test-work' / ('aitools-' + uuid.uuid4().hex)
    root.mkdir(parents=True)
    try:
        yield str(root)
    finally:
        shutil.rmtree(root)

import aitools_hooks as hooks

class HookTests(unittest.TestCase):
    def test_windows_paths_spaces_and_existing_hooks_preserved(self):
        own = hooks.proposal(Path('C:/Client Project/Kit'), Path('C:/Python 3/python.exe'))
        command = own['hooks']['SessionStart'][0]['hooks'][0]['commandWindows']
        self.assertTrue(command.startswith('powershell.exe -NoProfile -NonInteractive -EncodedCommand '))
        self.assertIn("'C:", hooks.windows_launcher_scripts(own)['SessionStart'])
        previous = {'description': 'client', 'hooks': {'SessionStart': [{'hooks': [{'type': 'command', 'command': 'client-original'}]}]}}
        merged, receipt = hooks.merge_owned(previous, own)
        self.assertEqual(merged['hooks']['SessionStart'][0], previous['hooks']['SessionStart'][0])
        self.assertEqual(hooks.restore_owned(merged, receipt), previous)
        merged['hooks']['SessionStart'][-1]['hooks'][0]['command'] = 'client changed'
        with self.assertRaises(ValueError): hooks.restore_owned(merged, receipt)
    def test_invalid_json_and_missing_interpreter_fail_open(self):
        self.assertEqual(hooks.run_advisory('SessionStart', '{bad', KIT, interpreter='missing-python')[0], {})
        self.assertEqual(hooks.run_advisory('SessionStart', '{}', KIT, interpreter='missing-python')[0], {})
    def test_failure_and_blocking_output_do_not_change_gates(self):
        class Result:
            returncode = 1
            stdout = '{"continue":false,"decision":"block"}'
        with patch.object(hooks.subprocess, 'run', return_value=Result()):
            self.assertEqual(hooks.run_advisory('SessionStart', '{}', KIT)[0], {})
        Result.returncode = 0
        with patch.object(hooks.subprocess, 'run', return_value=Result()):
            output, state = hooks.run_advisory('SessionStart', '{}', KIT)
            self.assertNotIn('continue', output)
            self.assertNotIn('decision', output)
    def test_fixture_all_three_events_no_authentication_or_remote(self):
        for event in ('SessionStart', 'UserPromptSubmit', 'PostToolUse'):
            with self.subTest(event=event):
                class Result:
                    returncode = 0
                    stdout = json.dumps({'hookSpecificOutput': {'hookEventName': event, 'additionalContext': 'fixture advisory'}})
                with patch.object(hooks.subprocess, 'run', return_value=Result()) as run:
                    output, state = hooks.run_advisory(event, json.dumps({'hook_event_name': event, 'cwd': 'C:/Project With Spaces', 'tool_name': 'Bash', 'tool_input': {'command': 'databricks current-user me'}, 'tool_response': 'fixture auth error'}), KIT)
                    self.assertEqual(output['hookSpecificOutput']['hookEventName'], event)
                    self.assertFalse(run.call_args.kwargs.get('shell', False))
                    self.assertEqual(state, 'fixture_or_invocation_only')
    def test_actual_upstream_fixtures_offline_no_native_observation(self):
        fixtures = {
            'SessionStart': {'source': 'startup'},
            'UserPromptSubmit': {'prompt': 'Inspect Databricks jobs', 'session_id': ''},
            'PostToolUse': {'tool_name': 'Bash', 'tool_input': {'command': 'databricks current-user me'}, 'tool_response': {'stderr': 'cannot configure default credentials'}},
        }
        with workspace_temp() as tmp:
            env = dict(os.environ, PATH='', DATABRICKS_CONFIG_FILE=str(Path(tmp) / 'missing-config'))
            for key in list(env):
                if key.startswith('DATABRICKS_') and key != 'DATABRICKS_CONFIG_FILE':
                    del env[key]
            for event, payload in fixtures.items():
                payload.update({'cwd': tmp, 'hook_event_name': event})
                with self.subTest(event=event):
                    result = subprocess.run([sys.executable, str(KIT / 'scripts/crea/aitools.py'), 'hook', '--event', event], input=json.dumps(payload), capture_output=True, text=True, encoding='utf-8', env=env, timeout=10)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    output = json.loads(result.stdout)
                    self.assertEqual(output['hookSpecificOutput']['hookEventName'], event)
                    self.assertIn('Advisory only', output['hookSpecificOutput']['additionalContext'])
                    self.assertNotIn('decision', output)
                    self.assertEqual(list(Path(tmp).iterdir()), [])
    def test_windows_proposal_runs_with_spaces_and_apostrophe(self):
        if sys.platform != 'win32':
            self.skipTest('Windows launcher contract')
        with workspace_temp() as tmp:
            # Project and interpreter already live under paths containing spaces.
            command = hooks.proposal(KIT)['hooks']['UserPromptSubmit'][0]['hooks'][0]['commandWindows']
            payload = json.dumps({'hook_event_name': 'UserPromptSubmit', 'prompt': 'Databricks jobs', 'session_id': ''})
            result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command], input=payload, capture_output=True, text=True, encoding='utf-8', timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['hookSpecificOutput']['hookEventName'], 'UserPromptSubmit')
            cmd_result = subprocess.run(['cmd.exe', '/d', '/s', '/c', command], input=payload, capture_output=True, text=True, encoding='utf-8', timeout=15)
            self.assertEqual(cmd_result.returncode, 0, cmd_result.stderr)
            self.assertEqual(json.loads(cmd_result.stdout)['hookSpecificOutput']['hookEventName'], 'UserPromptSubmit')
            escaped = hooks.windows_launcher_scripts(hooks.proposal(Path("C:/Client's $Project/Kit")))['SessionStart']
            self.assertIn("Client''s $Project", escaped)
    def test_restore_preserves_unrelated_changes_and_empty_events(self):
        previous = {'hooks': {'Stop': [], 'SessionStart': []}, 'description': 'client'}
        merged, receipt = hooks.merge_owned(previous, hooks.proposal(KIT))
        merged['description'] = 'changed by client'
        merged['hooks']['Stop'].append({'hooks': [{'type': 'command', 'command': 'client-new'}]})
        restored = hooks.restore_owned(merged, receipt)
        self.assertEqual(restored['description'], 'changed by client')
        self.assertEqual(len(restored['hooks']['Stop']), 1)
        self.assertEqual(restored['hooks']['SessionStart'], [])
    def test_missing_resources_never_included(self):
        with workspace_temp() as tmp:
            state = hooks.inspect_hooks(Path(tmp), Path(tmp))
        self.assertFalse(state['included'])
        self.assertEqual(state['authorized'], 'unknown')
        self.assertEqual(state['observed'], 'not_run')

if __name__ == '__main__': unittest.main()
