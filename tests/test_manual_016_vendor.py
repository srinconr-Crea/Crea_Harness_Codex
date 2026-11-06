"""Offline contracts for the immutable Databricks vendor selection."""
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class VendorTests(unittest.TestCase):
    def module(self):
        spec = importlib.util.spec_from_file_location('vendor016', ROOT / 'scripts/sync_databricks_016.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_selection_closes_reviewed_dependencies(self):
        m = self.module()
        self.assertEqual(len(m.SELECTED), 28)
        self.assertTrue({'databricks-serverless', 'databricks-genie-agents', 'databricks-vector-search', 'databricks-sandbox'} <= set(m.SELECTED))
        self.assertNotIn('spark-python-data-source', m.SELECTED)

    def test_archive_rejects_traversal_and_unpinned_root(self):
        m = self.module()
        for name in ['other-root/LICENSE', m.ARCHIVE_ROOT + '../escape']:
            p = io.BytesIO()
            with zipfile.ZipFile(p, 'w') as z:
                z.writestr(name, b'x')
            p.seek(0)
            with self.assertRaises(ValueError):
                m.read_archive(p)

    def test_upstream_nested_mlflow_and_apps_links_preserved(self):
        m = self.module()
        path = '.agents/skills/databricks-mlflow-evaluation/references/mlflow-agent-improvement/guide.md'
        content = b'[tracing](../../../databricks-mlflow-tracing/references/mlflow-trace-analysis/guide.md)'
        fixed, patches = m.patch_payload(path, content)
        self.assertEqual(fixed, content)
        self.assertEqual(patches, [])
        fixed2, patches2 = m.patch_payload('.agents/skills/databricks-apps/references/appkit/proto-first.md', b'[contracts](proto-contracts.md)')
        self.assertEqual(patches2, [])

    def test_pinned_distributed_inventory_is_complete_and_byte_verified(self):
        m = self.module()
        kit = ROOT / 'artifacts/crea-manual-kit-0.1.6'
        result = m.verify(kit)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['skill_count'], 28)
        self.assertGreater(result['file_count'], 300)


if __name__ == '__main__':
    unittest.main()
