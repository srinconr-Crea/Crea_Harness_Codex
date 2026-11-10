"""Binding personal: no puede cambiar política y participa en la ejecución."""
import copy
import json
import sys
import unittest

import test_testing_adapters as legacy
from testing import workflow
from testing.common import read, write

try:
    import entorno_local
except ImportError:
    entorno_local = None


class LocalEnvironmentTests(unittest.TestCase):
    setUp = legacy.AdaptersTests.setUp
    cleanup = legacy.AdaptersTests.cleanup
    local_setup = legacy.AdaptersTests.local_setup
    write = legacy.AdaptersTests.write
    git = legacy.AdaptersTests.git
    init_git = legacy.AdaptersTests.init_git

    def test_binding_resolves_without_changing_shared_settings(self):
        self.assertIsNotNone(entorno_local, 'Local resolver is missing')
        settings = {'python_executable': None, 'local_environment_path': '.crea/local.json'}
        self.write('.crea/local.json', json.dumps({'schema_version': '1.0', 'python_executable': sys.executable}))
        frozen = copy.deepcopy(settings)
        actual = entorno_local.resolve(self.root, settings)
        self.assertEqual(actual['python_executable'], sys.executable)
        self.assertNotIn('local_environment_path', actual)
        self.assertEqual(settings, frozen)

    def test_policy_overrides_and_conflicting_sources_are_rejected(self):
        self.assertIsNotNone(entorno_local)
        settings = {'python_executable': None, 'local_environment_path': '.crea/local.json'}
        self.write('.crea/local.json', json.dumps({'schema_version':'1.0', 'python_executable':sys.executable, 'required_checks':[]}))
        with self.assertRaises(ValueError): entorno_local.resolve(self.root, settings)
        self.write('.crea/local.json', json.dumps({'schema_version':'1.0', 'python_executable':sys.executable}))
        with self.assertRaises(ValueError): entorno_local.resolve(self.root, {**settings, 'python_executable':sys.executable})
        with self.assertRaises(ValueError): entorno_local.resolve(self.root, {**settings, 'local_environment_path':'../local.json'})

    def test_legacy_resolution_is_unchanged(self):
        self.assertIsNotNone(entorno_local)
        legacy_settings = {'python_executable': sys.executable, 'checks': {}}
        self.assertEqual(entorno_local.resolve(self.root, legacy_settings), legacy_settings)

    def test_shared_binding_plan_is_rebuilt_and_alias_does_not_change_python_identity(self):
        base, policy, execution, outputs = self.local_setup()
        self.write('.gitignore', '.crea/local.json\n')
        self.git('add', '--', '.gitignore'); self.git('commit', '-m', 'local exclusions')
        base = self.git('rev-parse', 'HEAD')
        settings = read(execution)
        settings['python_executable'] = None
        settings['local_environment_path'] = '.crea/local.json'
        write(execution, settings)
        self.write('.crea/local.json', json.dumps({'schema_version':'1.0', 'python_executable':sys.executable}))
        plan = workflow.make_plan(self.root, policy, execution, base, ['CA01'])
        self.assertEqual(plan['status'], 'ready', plan['blockers'])
        self.assertTrue(workflow.current(self.root, policy, execution, plan))
        self.write('.crea/local.json', json.dumps({'schema_version':'1.0', 'python_executable':sys.executable, 'databricks_profile':'personal'}))
        self.assertTrue(workflow.current(self.root, policy, execution, plan))
        result = workflow.run(self.root, policy, execution, plan)
        self.assertEqual(workflow.gate(self.root, policy, execution, plan, result)['status'], 'passed')

    def test_binding_with_attempts_preserves_configuration_and_rejects_transplanted_receipts(self):
        import test_testing_lifecycle as lifecycle
        from testing.common import file_hash
        base,policy,execution=lifecycle.LifecycleTests.fixture(self)
        self.write('.gitignore','.crea/local.json\n')
        self.git('add','--','.gitignore');self.git('commit','-m','personal binding exclusion')
        base=self.git('rev-parse','HEAD')
        settings=read(execution);settings['python_executable']=None;settings['local_environment_path']='.crea/local.json';write(execution,settings)
        self.write('.crea/local.json',json.dumps({'schema_version':'1.0','python_executable':sys.executable}))
        before=(file_hash(policy),file_hash(execution))
        first=workflow.make_plan(self.root,policy,execution,base,['CA01','CA02'],change='one',attempt='1')
        result=workflow.run(self.root,policy,execution,first)
        self.assertEqual(workflow.gate(self.root,policy,execution,first,result)['status'],'passed')
        second=workflow.make_plan(self.root,policy,execution,base,['CA01','CA02'],change='two',attempt='2')
        self.assertTrue(workflow.current(self.root,policy,execution,second))
        self.assertEqual(workflow.gate(self.root,policy,execution,second,result)['status'],'blocked')
        own=workflow.run(self.root,policy,execution,second)
        self.assertEqual(workflow.gate(self.root,policy,execution,second,own)['status'],'passed')
        self.assertEqual(before,(file_hash(policy),file_hash(execution)))


if __name__ == '__main__':
    unittest.main()
