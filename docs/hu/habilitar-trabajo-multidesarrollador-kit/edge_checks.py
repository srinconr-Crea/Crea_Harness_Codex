"""Supplemental reproducible local boundary checks; not distributed business tests."""
from pathlib import Path
import json
import os
import sys
import unittest

ROOT=Path(__file__).resolve().parents[3]
KIT=ROOT/'artifacts/crea-manual-kit-0.1.9'
sys.path.insert(0,str(KIT/'tests/crea'))
import test_target_compatibility as fixtures
import test_content_v3 as content
import test_local_environment as local
import compatibilidad
from testing import workflow,git_adapter
from testing.common import read,write
from team_common import safe_path


class AdditionalChecks(unittest.TestCase):
    setUp=fixtures.TargetCompatibilityTests.setUp
    cleanup=fixtures.TargetCompatibilityTests.cleanup
    write=fixtures.TargetCompatibilityTests.write
    git=fixtures.TargetCompatibilityTests.git
    init_git=fixtures.TargetCompatibilityTests.init_git
    graph=fixtures.TargetCompatibilityTests.graph
    simulation=fixtures.TargetCompatibilityTests.simulation
    review=fixtures.TargetCompatibilityTests.review
    local_setup=local.LocalEnvironmentTests.local_setup

    def test_rename_is_present_on_both_sides_of_scope(self):
        p,h,s=self.graph()
        self.git('mv','src/a.py','src/renamed.py');self.git('commit','-m','rename producer')
        h['scope']['head']=self.git('rev-parse','HEAD')
        result=compatibilidad.inspect(self.root,p,h,s,simulation=self.simulation(h,s))
        rows=result['ranges']['story_changes']
        self.assertTrue(any(row['old_path']=='src/a.py' and row['path']=='src/renamed.py' for row in rows))
        self.assertIn('src/a.py',result['review_paths']);self.assertIn('src/renamed.py',result['review_paths'])

    def test_same_file_nonoverlapping_changes_can_be_reviewed_compatible(self):
        p,h,s=self.graph()
        self.git('switch','fixture-base')
        lines=[str(n)+'\n' for n in range(20)]
        self.write('docs/shared.md',''.join(lines));self.git('add','--','docs/shared.md');self.git('commit','-m','shared contract')
        base=self.git('rev-parse','HEAD');self.git('switch','-c','quality-compatible')
        targetlines=list(lines);targetlines[0]='target addition\n'
        self.write('docs/shared.md',''.join(targetlines));self.git('add','--','docs/shared.md');self.git('commit','-m','target compatible edit')
        target=self.git('rev-parse','HEAD');self.git('switch','-c','feature/compatible',base)
        lines[-1]='feature addition\n';self.write('docs/shared.md',''.join(lines));self.git('add','--','docs/shared.md');self.git('commit','-m','feature compatible edit')
        h['scope'].update({'base':base,'head':self.git('rev-parse','HEAD')});h['scope']['git_delivery']['branch_start_sha']=base
        p['delivery']['pr_target_branch']='quality-compatible';s.update({'target_branch':'quality-compatible','target_sha':target})
        p['context_management']['components'][1]['paths'].append('docs/shared.md')
        p['context_management']['components'][1]['documents']=[{'path':'docs/shared.md','kind':'technical','roles':['reviewer'],'phases':['revision']}]
        simulation=self.simulation(h,s);self.assertEqual(simulation['status'],'clean')
        first=compatibilidad.inspect(self.root,p,h,s,simulation=simulation)
        report=compatibilidad.inspect(self.root,p,h,s,simulation=simulation,semantic_review=self.review(first))
        self.assertEqual(report['outcome'],'compatible')

    def test_interpreter_change_invalidates_even_unchanged_shared_execution(self):
        base,p,e,_=self.local_setup()
        self.write('.gitignore','.crea/local.json\n');self.git('add','--','.gitignore');self.git('commit','-m','personal exclusion')
        base=self.git('rev-parse','HEAD')
        settings=read(e);settings['python_executable']=None;settings['local_environment_path']='.crea/local.json';write(e,settings)
        self.write('.crea/local.json',json.dumps({'schema_version':'1.0','python_executable':sys.executable}))
        before=e.read_bytes();plan=workflow.make_plan(self.root,p,e,base,['CA01'])
        other=getattr(sys,'_base_executable',sys.executable)
        self.assertNotEqual(str(Path(other).resolve()),str(Path(sys.executable).resolve()))
        self.write('.crea/local.json',json.dumps({'schema_version':'1.0','python_executable':other}))
        self.assertFalse(workflow.current(self.root,p,e,plan));self.assertEqual(before,e.read_bytes())

    def test_content_v3_publication_requires_exact_reviewed_observation_bytes(self):
        base,name,projection,data=content.ContentV3Tests.fixture(self)
        self.write('src/value.py','value = 2\n');self.write(name,json.dumps(data))
        reviewed=git_adapter.content_view(self.root,base,[],projection)
        self.git('add','--','src/value.py',name);self.git('commit','-m','reviewed observation and code')
        self.assertTrue(git_adapter.verify_commit(self.root,base,'HEAD',reviewed,['src/value.py',name]))
        self.write(name,json.dumps({**data,'status':'undetermined'}))
        now=git_adapter.content_view(self.root,base,[],projection)
        with self.assertRaisesRegex(ValueError,'COMMIT_DIFFERS_FROM_REVIEWED_METADATA'):
            git_adapter.verify_commit(self.root,base,'HEAD',now,['src/value.py',name])

    def test_local_binding_hardlink_is_rejected(self):
        import entorno_local
        self.init_git();original=self.write('state.json',json.dumps({'schema_version':'1.0','python_executable':sys.executable}))
        (self.root/'.crea').mkdir();os.link(original,self.root/'.crea/local.json')
        with self.assertRaises(ValueError):entorno_local.binding(self.root)

    def test_two_checkout_bindings_use_two_existing_interpreters_with_same_catalog(self):
        import shutil
        import test_testing_adapters as legacy
        from testing.common import digest,file_hash
        first=legacy.AdaptersTests();second=legacy.AdaptersTests();first.setUp();second.setUp()
        try:
            base,p,e,_=first.local_setup()
            first.write('.gitignore','.crea/local.json\n')
            # Use already installed pytest for both prepared interpreters; no install.
            site=Path(sys.prefix)/'Lib/site-packages'
            runner='import sys\nsys.path.insert(0,'+repr(str(site))+')\nimport pytest\nraise SystemExit(pytest.main(["-c","pytest.ini","-q","-p","no:cacheprovider","tests/test_codes.py",*sys.argv[1:]]))\n'
            first.write('runner.py',runner)
            policy=read(p);policy['checks'][0]['argv']=['python','runner.py','--junitxml=docs/hu/synthetic/pruebas/junit-unit.xml']
            policy['checks'][0]['inputs'].append('runner.py');policy['rules'][0]['paths'].append('runner.py');policy['rules'][0]['paths'].append('.gitignore')
            write(p,policy);settings=read(e);settings.update({'python_executable':None,'local_environment_path':'.crea/local.json','reviewed_policy_digest':digest(policy)});write(e,settings)
            shutil.copytree(first.root,second.root,dirs_exist_ok=True)
            shared=(file_hash(p),file_hash(e));results=[];plans=[]
            for fixture,interpreter in [(first,sys.executable),(second,sys._base_executable)]:
                fixture.write('.crea/local.json',json.dumps({'schema_version':'1.0','python_executable':interpreter}))
                plan=workflow.make_plan(fixture.root,fixture.root/'policy.json',fixture.root/'execution.json',base,['CA01','CA02'])
                result=workflow.run(fixture.root,fixture.root/'policy.json',fixture.root/'execution.json',plan)
                gate=workflow.gate(fixture.root,fixture.root/'policy.json',fixture.root/'execution.json',plan,result)
                self.assertEqual(gate['status'],'passed',result)
                self.assertEqual(shared,(file_hash(fixture.root/'policy.json'),file_hash(fixture.root/'execution.json')))
                plans.append(plan);results.append(result)
            self.assertNotEqual(plans[0]['plan_id'],plans[1]['plan_id'])
            self.assertNotEqual(results[0]['records'][0]['environment_id'],results[1]['records'][0]['environment_id'])
            self.assertEqual(workflow.gate(second.root,second.root/'policy.json',second.root/'execution.json',plans[1],results[0])['status'],'blocked')
        finally:
            first.doCleanups();second.doCleanups()

    def test_snapshot_ignores_stale_tracking_custom_refspec_and_detects_race(self):
        from unittest.mock import patch
        import entrega
        p,h,s=self.graph();remote=self.root/'remote.git'
        self.git('init','--bare',str(remote));self.git('remote','add','origin',str(remote))
        self.git('push','origin','quality:refs/heads/quality','feature/HU002:refs/heads/feature/HU002')
        p['project']['repository']['url']=str(remote)
        self.git('config','remote.origin.fetch','+refs/heads/feature/*:refs/remotes/origin/feature/*')
        self.git('update-ref','refs/remotes/origin/quality',h['scope']['base'])
        self.write('docs/plantillas/git-target-snapshot.schema.json',(KIT/'docs/plantillas/git-target-snapshot.schema.json').read_text())
        heads=self.git('for-each-ref','--format=%(refname) %(objectname)','refs/heads');index=(self.root/'.git/index').read_bytes()
        actual=entrega.snapshot(self.root,p,'HU002','extra1')
        self.assertEqual(actual['target_sha'],s['target_sha']);self.assertEqual(actual['status'],'verified')
        self.assertEqual(self.git('rev-parse','refs/remotes/origin/quality'),h['scope']['base'])
        collision=entrega.remote_sha(self.root,'origin','feature/HU002')
        self.assertEqual(collision,(h['scope']['head'],'verified'))
        with patch.object(entrega,'remote_sha',side_effect=[(s['target_sha'],'verified'),(h['scope']['base'],'verified')]):
            raced=entrega.snapshot(self.root,p,'HU002','extra2')
        self.assertEqual(raced['status'],'unverified');self.assertFalse(raced['objects_available'])
        self.assertEqual(heads,self.git('for-each-ref','--format=%(refname) %(objectname)','refs/heads'))
        self.assertEqual(index,(self.root/'.git/index').read_bytes())

    def test_online_preparation_errors_are_sanitized_and_do_not_retry_login(self):
        from unittest.mock import patch
        import subprocess
        import test_developer_preparation as prep
        self.init_git()
        for response in [subprocess.CompletedProcess([],1,b'',b'password=private'),
                         subprocess.TimeoutExpired(['az'],1),OSError('network')]:
            with self.subTest(response=type(response).__name__):
                kwargs={'side_effect':response} if isinstance(response,Exception) else {'return_value':response}
                with patch.object(prep.preparation,'process',**kwargs) as calls:
                    result=prep.preparation.checked_read(['az','repos','show'],self.root,'azure_repository')
                self.assertEqual(calls.call_count,1);self.assertEqual(result['status'],'connection_error' if isinstance(response,subprocess.TimeoutExpired) else 'unverified')
                self.assertNotIn('private',json.dumps(result))

    def test_changed_history_is_visible_in_git_but_not_loaded_as_contract(self):
        p,h,s=self.graph()
        own='openspec/changes/HU002/specs/local/spec.md'
        unrelated='openspec/changes/other/proposal.md'
        archived='openspec/changes/archive/2026-01-01-old/specs/private/spec.md'
        for name in [own,unrelated,archived]:self.write(name,'bounded contract or unrelated history\n')
        report=compatibilidad.inspect(self.root,p,h,s)
        paths={row['path'] for row in report['document_refs']}
        self.assertIn(own,paths)
        self.assertNotIn(unrelated,paths);self.assertNotIn(archived,paths)
        self.assertTrue({unrelated,archived}.issubset(report['review_paths']))


if __name__=='__main__':unittest.main()
