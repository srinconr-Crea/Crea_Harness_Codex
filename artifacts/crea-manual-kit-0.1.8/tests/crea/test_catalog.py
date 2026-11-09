"""Discovery metadata only and explicit safe outputs, before setup."""
from pathlib import Path
import test_testing_adapters as legacy
import unittest
from unittest.mock import patch
from testing import catalog
from testing.common import ASSETS,KIT,read

class CatalogTests(unittest.TestCase):
    setUp=legacy.AdaptersTests.setUp
    cleanup=legacy.AdaptersTests.cleanup
    def test_surfaces_sensitive_installed_and_bodies_not_opened(self):
        root=self.root
        for name in ['qa/test_own.py','tests/crea/test_kit.py','evals/test_agent.py','.venv/test_installed.py','qa/test_secret.py']:
            p=root/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text('raise RuntimeError("must not import")\n',encoding='utf-8')
        policy=read(ASSETS/'policy.template.json')
        policy['lifecycle']={'schema_version':'1.0','locations':[{'path':'qa','kind':'tests'},{'path':'evals','kind':'evals'}],'test_inventory':[]}
        with patch.object(Path,'read_bytes',side_effect=AssertionError('suite body opened')),patch('subprocess.Popen',side_effect=AssertionError('suite subprocess')):
            result=catalog.discover(root,policy)
        rows={r['path']:r for r in result['rows']}
        self.assertEqual(set(rows),{'qa/test_own.py','tests/crea/test_kit.py','evals/test_agent.py'})
        self.assertEqual(rows['tests/crea/test_kit.py']['surface'],'kit')
        self.assertEqual(rows['evals/test_agent.py']['surface'],'agent_evals')
        self.assertEqual(result['execution'],'not_run')
