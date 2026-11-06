import importlib.util
import json
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

import aitools_inventory as ai

class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = workspace_temp()
        self.root = Path(self.tmp.__enter__())
        self.addCleanup(self.tmp.__exit__, None, None, None)
        (self.root / 'docs').mkdir()
        self.config = self.root / 'docs/proyecto.json'
        self.config.write_text('{}')
        self.lock = {'revision': 'a' * 40, 'selected_skills': ['databricks-demo'], 'files': [], 'mandatory_dependencies': {}}
        self.skill(self.root / '.agents/skills/demo', 'databricks-demo', 'official')
    def skill(self, folder, name, body):
        folder.mkdir(parents=True)
        (folder / 'SKILL.md').write_text('---\nname: '+name+'\n---\n'+body)
    def preview(self, surfaces=None):
        return ai.preview(self.config, kit_root=self.root, lock=self.lock, surfaces=surfaces or {})
    def test_duplicate_identity_and_custom_version_are_conflicts_without_writes(self):
        other = self.root / '.codex/skills/demo'
        self.skill(other, 'databricks-demo', 'custom version')
        before = other.joinpath('SKILL.md').read_bytes()
        report = self.preview({'legacy': other.parent})
        self.assertEqual(report['duplicates'][0]['name'], 'databricks-demo')
        self.assertEqual(report['duplicates'][0]['status'], 'conflict')
        self.assertEqual(before, other.joinpath('SKILL.md').read_bytes())
    def test_missing_dependency_prevents_complete_selection(self):
        self.lock['mandatory_dependencies'] = {'databricks-demo': ['databricks-absent']}
        report = self.preview()
        self.assertEqual(report['selection_status'], 'incomplete')
        self.assertIn('databricks-absent', str(report['issues']))
    def test_inaccessible_surface_is_unknown_not_empty(self):
        report = self.preview({'global': None})
        self.assertEqual(report['surfaces']['global']['status'], 'unknown')
        self.assertEqual(report['duplicate_coverage'], 'partial')
    def test_permission_error_is_unknown(self):
        with patch.object(ai, 'scan_surface', side_effect=PermissionError('denied')):
            report = self.preview({'global': self.root})
        self.assertEqual(report['surfaces']['global']['status'], 'unknown')
    def test_export_exclusive_confined_and_no_implicit_directories(self):
        out = self.root / 'report.json'
        ai.export_new({'ok': True}, out, self.root)
        with self.assertRaises((ValueError, FileExistsError)):
            ai.export_new({}, out, self.root)
        with self.assertRaises(ValueError):
            ai.export_new({}, self.root.parent / 'escape.json', self.root)
        self.assertEqual(json.loads(out.read_text()), {'ok': True})
    def test_real_bundle_validation_and_missing_hook_dependency(self):
        result = ai.validate_bundle(KIT)
        self.assertGreaterEqual(result['skills'], 24)
        self.assertFalse(result['native_hooks_observed'])
        broken = json.loads((KIT / 'resources/databricks-aitools/upstream-lock.json').read_text())
        broken['mandatory_dependencies']['databricks-core'] = ['missing-required']
        with patch.object(ai, 'read_json', return_value=broken):
            with self.assertRaisesRegex(ValueError, 'MISSING_MANDATORY_DEPENDENCY'):
                ai.validate_bundle(KIT)
    def test_preview_never_calls_transport(self):
        with patch('subprocess.run', side_effect=AssertionError('No process in preview')):
            self.preview({'global': None})
    def test_missing_locked_resource_is_incomplete(self):
        self.lock['files'] = [{'path': 'resources/missing.py', 'distributed_sha256': 'f'*64}]
        self.assertEqual(self.preview()['selection_status'], 'incomplete')

if __name__ == '__main__': unittest.main()
