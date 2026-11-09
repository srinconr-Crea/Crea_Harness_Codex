"""Distribución candidata 0.1.7: preservación y adopción por diff, sin instalar."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
PACK=ROOT/'scripts/package_manual_017.py'

class DistributionTests(unittest.TestCase):
    def module(self):
        self.assertTrue(PACK.is_file(),'empaquetador nuevo no implementado')
        spec=importlib.util.spec_from_file_location('package017',PACK)
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        return module

    def test_packager_rejects_every_historical_target(self):
        m=self.module()
        for version in ('0.1.3','0.1.4','0.1.5','0.1.6'):
            with self.assertRaises(ValueError): m.assert_target(ROOT/('artifacts/crea-manual-kit-'+version))
        m.assert_target(m.KIT)
        with self.assertRaises(ValueError): m.write_archive(m.KIT,ROOT/'artifacts/crea-manual-kit-0.1.6.zip')

    def test_historical_baseline_is_unchanged(self):
        m=self.module()
        baseline=m.read(ROOT/'docs/hu/gestionar-contexto-evolutivo-proyecto/baseline.json')
        self.assertTrue(m.verify_baseline(ROOT,baseline)['source_preserved'])

if __name__=='__main__': unittest.main()
