"""Preparación personal conserva el checkout y hace explícitos sus efectos."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_testing_adapters as legacy
from testing.common import KIT, read, file_hash

module_path=KIT/'scripts/crea/preparar-desarrollador.py'
preparation=None
if module_path.is_file():
    spec=importlib.util.spec_from_file_location('crea_developer_preparation',module_path)
    preparation=importlib.util.module_from_spec(spec); spec.loader.exec_module(preparation)


class DeveloperPreparationTests(unittest.TestCase):
    setUp=legacy.AdaptersTests.setUp
    cleanup=legacy.AdaptersTests.cleanup
    write=legacy.AdaptersTests.write
    git=legacy.AdaptersTests.git
    init_git=legacy.AdaptersTests.init_git

    def test_incomplete_shared_setup_is_not_overwritten_or_declared_ready(self):
        self.assertIsNotNone(preparation,'Preparation helper is missing')
        self.init_git()
        source=self.write('docs/proyecto.json',json.dumps(read(KIT/'docs/proyecto.json')))
        before=file_hash(source)
        with patch.object(preparation,'online_checks',side_effect=AssertionError('implicit remote read')):
            result=preparation.inspect_environment(self.root)
        self.assertEqual(result['status'],'blocked')
        self.assertIn('PROJECT_SETUP_INCOMPLETE',[x['code'] for x in result['pending']])
        self.assertEqual(before,file_hash(source))

    def test_bind_preview_and_repeat_are_local_and_idempotent(self):
        self.assertIsNotNone(preparation)
        self.init_git(); original=self.git('rev-parse','HEAD')
        preview=preparation.bind(self.root,sys.executable)
        self.assertEqual(preview['status'],'preview')
        self.assertFalse((self.root/'.crea/local.json').exists())
        first=preparation.bind(self.root,sys.executable,apply=True)
        self.assertEqual(first['status'],'updated')
        path=self.root/'.crea/local.json'; stamp=path.stat().st_mtime_ns
        again=preparation.bind(self.root,sys.executable,apply=True)
        self.assertEqual(again['status'],'unchanged')
        self.assertEqual(stamp,path.stat().st_mtime_ns)
        self.assertEqual(original,self.git('rev-parse','HEAD'))
        self.assertEqual(read(path),{'schema_version':'1.0','python_executable':sys.executable})

    def test_missing_dependencies_under_no_site_produce_json_without_login_or_install(self):
        self.assertIsNotNone(preparation)
        self.init_git(); self.write('docs/proyecto.json',json.dumps(read(KIT/'docs/proyecto.json')))
        result=subprocess.run([sys.executable,'-S','-B',str(module_path),'inspect','--repo',str(self.root)],capture_output=True,text=True)
        self.assertNotIn('Traceback',result.stderr)
        data=json.loads(result.stdout)
        self.assertIn('VALIDATION_DEPENDENCY_UNAVAILABLE',[x['code'] for x in data['pending']])
        self.assertFalse((self.root/'.crea').exists())

    def test_remote_checks_do_not_credit_write_permissions_or_boards(self):
        self.assertIsNotNone(preparation)
        project=read(KIT/'docs/proyecto.json')
        project['project']['repository'].update({'provider':'azure_devops','url':'https://dev.azure.com/org/proj/_git/repo',
            'organization':'https://dev.azure.com/org','project':'proj','name_or_id':'repo'})
        calls=[]
        def run(argv,root=None,**kwargs):
            calls.append(argv)
            return subprocess.CompletedProcess(argv,0,b'{"id":"repo","remoteUrl":"https://dev.azure.com/org/proj/_git/repo"}',b'')
        with patch.object(preparation,'process',side_effect=run):
            values=preparation.online_checks(self.root,project)
        self.assertFalse(values['write_permissions_verified'])
        self.assertTrue(any(x[:3]==['az','repos','show'] for x in calls))
        self.assertFalse(any(any(w in x for w in ['boards','pipelines','login','create','update','install']) for x in calls))

    def test_dependencies_are_checked_in_selected_python_not_only_the_host(self):
        self.assertIsNotNone(preparation)
        self.init_git();project=read(KIT/'docs/proyecto.json')
        self.write('docs/proyecto.json',json.dumps(project))
        settings=read(KIT/'docs/pruebas/execution.json')
        settings['local_environment_path']='.crea/local.json'
        self.write('docs/pruebas/execution.json',json.dumps(settings))
        self.write('docs/pruebas/policy.json',json.dumps(read(KIT/'docs/pruebas/policy.json')))
        selected=Path(sys.base_prefix)/('python.exe' if sys.platform=='win32' else 'bin/python')
        self.write('.crea/local.json',json.dumps({'schema_version':'1.0','python_executable':str(selected)}))
        report=preparation.inspect_environment(self.root)
        self.assertEqual(report['selected_python'],str(selected))
        self.assertIn('VALIDATION_DEPENDENCY_UNAVAILABLE',[x['code'] for x in report['pending']])

    def test_tracked_personal_file_is_reported_without_removing_it(self):
        self.init_git();self.write('docs/proyecto.json',json.dumps(read(KIT/'docs/proyecto.json')))
        self.write('.crea/local.json',json.dumps({'schema_version':'1.0','python_executable':sys.executable}))
        self.git('add','--','.crea/local.json');self.git('commit','-m','previously tracked personal state')
        self.write('.gitignore','.crea/local.json\n')
        result=preparation.inspect_environment(self.root)
        self.assertIn('PERSONAL_FILE_TRACKED',[x['code'] for x in result['pending']])
        self.assertEqual(self.git('ls-files','--','.crea/local.json'),'.crea/local.json')

    def test_online_read_distinguishes_denial_connection_and_unverifiable_response(self):
        from subprocess import TimeoutExpired
        for response,expected in [(subprocess.CompletedProcess([],1,b'',b'HTTP 403 permission denied'),'access_denied'),
                                  (subprocess.CompletedProcess([],1,b'',b'could not resolve host'),'connection_error'),
                                  (subprocess.CompletedProcess([],1,b'',b'unknown error'),'unverified'),
                                  (TimeoutExpired(['az'],1),'connection_error'),(OSError('unavailable'),'unverified')]:
            kwargs={'side_effect':response} if isinstance(response,Exception) else {'return_value':response}
            with self.subTest(expected=expected),patch.object(preparation,'process',**kwargs) as called:
                result=preparation.checked_read(['az','repos','show'],self.root,'azure_repository')
                self.assertEqual(result['status'],expected)
                self.assertEqual(called.call_count,1)
                self.assertFalse(result.get('write_permissions_verified',False))

    def test_offline_diagnostic_identifies_configuration_and_local_remote_without_network(self):
        self.init_git();project=read(KIT/'docs/proyecto.json')
        project['project']['repository']['url']=str(self.root)
        self.git('remote','add','origin',str(self.root))
        config=self.write('docs/proyecto.json',json.dumps(project))
        with patch.object(preparation,'online_checks',side_effect=AssertionError('network')):
            result=preparation.inspect_environment(self.root)
        self.assertEqual(result['configuration_sha256'],file_hash(config))
        self.assertEqual(result['checkout_remote']['status'],'verified_local_identity')
        self.assertEqual(result['checkout_remote']['name'],'origin')
        self.assertEqual(result['remote']['status'],'not_run')


if __name__=='__main__': unittest.main()
