"""Auditoría genérica: identificadores de referencia llegan desde un input externo."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


class NeutralityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('neutrality', ROOT/'scripts/crea/audit_neutrality.py')
        cls.audit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.audit)

    def test_external_identifier_is_case_insensitive(self):
        hits = self.audit.scan_text('Config CLIENTE-DE-REFERENCIA', ['cliente-de-referencia'])
        self.assertIn('external_identifier', [h['category'] for h in hits])

    def test_detects_real_workspace_url(self):
        hits = self.audit.scan_text('https://adb-' + '1234567890123456.1.azuredatabricks.net', [])
        self.assertIn('workspace_url', [h['category'] for h in hits])

    def test_detects_absolute_personal_path(self):
        hits = self.audit.scan_text('C:' + '/Users/example/Documents/project', [])
        self.assertIn('absolute_windows_path', [h['category'] for h in hits])

    def test_official_documentation_is_allowed(self):
        self.assertEqual([], self.audit.scan_text('https://learn.microsoft.com/en-us/azure/databricks/notebooks/testing', []))

    def test_report_does_not_repeat_identifier(self):
        hits = self.audit.scan_text('secret-reference-identifier', ['secret-reference-identifier'])
        self.assertNotIn('secret-reference-identifier', str(hits))

    def test_generic_databricks_instructions_are_allowed(self):
        self.assertEqual([], self.audit.scan_text('Databricks: seleccionar perfil, catálogo y compute durante setup.', []))

    def test_report_redacts_identifiers_in_file_names(self):
        with patch.object(self.audit, 'entries', return_value=iter([('secret-reference.txt',b'neutral')])):
            report = self.audit.audit(Path('unused'),['secret-reference'])
        self.assertEqual('blocked',report['status'])
        self.assertNotIn('secret-reference',str(report))


if __name__ == '__main__':
    unittest.main()
