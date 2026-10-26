import importlib.util
from pathlib import Path
import unittest

KIT = Path(__file__).resolve().parents[1] / 'artifacts/crea-manual-kit-0.1.5'


class PackagingTests(unittest.TestCase):
    def load_package(self):
        path = KIT.parent.parent / 'scripts/package_manual_015.py'
        self.assertTrue(path.is_file(), 'Version-specific package entry point missing')
        spec = importlib.util.spec_from_file_location('package_015', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_package_cannot_target_previous_distributions(self):
        package = self.load_package()
        for name in ('crea-manual-kit-0.1.3', 'crea-manual-kit-0.1.4', 'other'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                package.assert_target(KIT.with_name(name))
        package.assert_target(KIT)

    def test_prior_source_manifests_and_upstream_are_preserved(self):
        report = self.load_package().preservation()
        self.assertGreater(report['source_manifest_files_verified'], 0)
        self.assertEqual(report['previous_versions_verified'], ['0.1.3', '0.1.4'])

    def test_zip_guard_checks_the_actual_versioned_filename(self):
        import json
        import uuid
        from unittest.mock import patch
        package = self.load_package()
        # TemporaryDirectory's restrictive Windows ACL is incompatible with this sandbox.
        scratch = KIT.parent.parent / '.test-data' / ('package-' + uuid.uuid4().hex)
        scratch.mkdir()
        if scratch.is_relative_to(KIT.parent.parent / '.test-data'):
            root = scratch
            target = root / 'artifacts/crea-manual-kit-0.1.5'
            target.mkdir(parents=True)
            for version in ('0.1.3', '0.1.4'):
                source = target.with_name('crea-manual-kit-' + version)
                source.mkdir()
                (source/'kit-manifest.json').write_text(json.dumps({'files': []}))
            archive = target.parent / 'crea-manual-kit-0.1.4.zip'
            archive.write_bytes(b'changed')
            archive.with_suffix('.zip.sha256').write_text('0' * 64)
            with patch.object(package, 'ROOT', root), patch.object(package, 'KIT', target):
                with self.assertRaisesRegex(ValueError, 'PREVIOUS_ZIP_CHANGED'):
                    package.preservation()


if __name__ == '__main__':
    unittest.main()
