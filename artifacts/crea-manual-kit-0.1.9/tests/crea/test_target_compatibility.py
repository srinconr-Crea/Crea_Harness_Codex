"""Casos A-F: repositorios Git locales y revisión semántica sintética explícita."""
import copy
import hashlib
import json
import subprocess
from pathlib import Path
import unittest

import test_testing_adapters as legacy
from testing.common import KIT, read
import entrega

try:
    import compatibilidad
except ImportError:
    compatibilidad=None


class TargetCompatibilityTests(unittest.TestCase):
    setUp=legacy.AdaptersTests.setUp
    cleanup=legacy.AdaptersTests.cleanup
    write=legacy.AdaptersTests.write
    git=legacy.AdaptersTests.git
    init_git=legacy.AdaptersTests.init_git

    def graph(self,dependent=False,shared=False):
        self.assertIsNotNone(compatibilidad,'Compatibility inspector is missing')
        self.init_git()
        self.write('.gitignore','.crea/tmp/\nremote.git/\n')
        self.write('src/a.py','unit = "pesos"\n')
        self.write('src/b.py','unit = "pesos"\n')
        self.write('docs/regla.md','regla base\n')
        self.write('docs/pruebas/policy.json',json.dumps({'checks':[],'rules':[]}))
        self.git('add','--','.gitignore','src','docs'); self.git('commit','-m','shared baseline')
        base=self.git('rev-parse','HEAD')
        self.git('switch','-c','quality')
        self.write('src/a.py','unit = "centavos"\n')
        if shared:self.write('docs/regla.md','aceptar solo activos\n')
        self.git('add','--','src/a.py','docs/regla.md');self.git('commit','-m','HU001 integrated')
        target=self.git('rev-parse','HEAD')
        self.git('switch','-c','feature/HU002',base)
        self.write('src/b.py','unit = "pesos"\nnew_behavior = True\n')
        if shared:self.write('docs/regla.md','aceptar tambien inactivos\n')
        self.git('add','--','src/b.py','docs/regla.md'); self.git('commit','-m','HU002 candidate')
        head=self.git('rev-parse','HEAD')
        p=read(KIT/'docs/proyecto.json');p['project']['base_branch']='fixture-base'
        p['project']['repository']['url']=str(self.root)
        p['delivery'].update({'pr_target_branch':'quality','compatibility':{'enabled':True}})
        p['context_management'].update({'enabled':True,'components':[
            {'id':'producer','paths':['src/a.py'],'dependencies':[],'documents':[]},
            {'id':'consumer','paths':['src/b.py'],'dependencies':['producer'] if dependent else [],'documents':[]} ]})
        h={'identity':{'change':'HU002'},'scope':{'base':base,'head':head,'candidate_digest':None,
             'git_delivery':{'branch_start_sha':base,'base_branch':'fixture-base','source_branch':'feature/HU002','remote':'origin'},
             'compatibility_artifacts':[]},'context':{},'evidence':{}}
        snap={'schema_version':'1.0','kind':'git_target_snapshot','change':'HU002','attempt':'1',
              'repository':list(entrega.repository_key(str(self.root))),'remote':'origin','base_branch':'fixture-base',
              'target_branch':'quality','target_sha':target,'status':'verified','objects_available':True,
              'observed_at':'2026-11-10T12:00:00Z','git_version':'git version fixture','limits':[]}
        return p,h,snap

    def review(self,report,status='compatible',findings=None):
        return {'schema_version':'1.0','kind':'target_semantic_review','change':'HU002',
                'source_sha':report['source_sha'],'target_sha':report['target_sha'],
                'scope_digest':report['scope_digest'],'status':status,'findings':findings or [],
                'reviewed_paths':report['review_paths'],'limitations':[]}

    def simulation(self,h,s):
        return compatibilidad.simulate(self.root,h['scope']['head'],s,self.root/'.crea/tmp/simulation')

    def test_A_independent_stories_continue_with_current_bounded_evidence(self):
        p,h,s=self.graph()
        simulation=self.simulation(h,s)
        first=compatibilidad.inspect(self.root,p,h,s,simulation=simulation)
        result=compatibilidad.inspect(self.root,p,h,s,simulation=simulation,semantic_review=self.review(first))
        self.assertEqual(result['outcome'],'compatible')
        self.assertEqual(result['freshness'],'current')
        self.assertEqual(result['affected_consumers'],[])
        self.assertEqual(result['source_branch'],'feature/HU002')

    def test_B_changed_producer_identifies_consumer_and_check(self):
        p,h,s=self.graph(dependent=True)
        p['validation']['testing']['policy_path']='policy.json'
        self.write('policy.json',json.dumps({'checks':[{'id':'consumer-check','inputs':['src/b.py'],'criteria':[]}],'rules':[]}))
        first=compatibilidad.inspect(self.root,p,h,s,simulation=self.simulation(h,s))
        self.assertEqual(first['outcome'],'requires_review')
        self.assertEqual(first['affected_consumers'],['consumer'])
        self.assertIn('consumer-check',[x['check_id'] for x in first['recommended_checks']])
        self.assertFalse(first['combined_tests_executed'])

    def test_C_same_rule_incompatible_and_D_clean_git_contradiction(self):
        for shared in [True,False]:
            with self.subTest(shared=shared):
                # Each scenario uses its own graph; never reuse a simulation directory.
                if shared: p,h,s=self.graph(shared=True)
                else:
                    # Preserve the first graph; use a nested independent fixture for D.
                    self.root=self.scratch/('semantic-'+self.root.name);self.root.mkdir()
                    p,h,s=self.graph(dependent=True)
                sim=self.simulation(h,s)
                first=compatibilidad.inspect(self.root,p,h,s,simulation=sim)
                finding={'id':'RULE-UNIT','type':'functional','reason':'Productor en centavos y contrato incompatible',
                         'owner':'reviewer','references':[{'path':'src/a.py','revision':s['target_sha'],
                         'sha256':hashlib.sha256(subprocess.check_output(['git','-C',str(self.root),'cat-file','blob',s['target_sha']+':src/a.py'])).hexdigest()}]}
                review=self.review(first,'conflict_detected',[finding])
                result=compatibilidad.inspect(self.root,p,h,s,simulation=sim,semantic_review=review)
                self.assertEqual(result['outcome'],'conflict_detected')
                if not shared:self.assertEqual(sim['status'],'clean')

    def test_E_target_move_invalidates_observation_without_mutating_story(self):
        p,h,s=self.graph();head=self.git('rev-parse','HEAD')
        current=copy.deepcopy(s);current['target_sha']=h['scope']['base']
        report=compatibilidad.inspect(self.root,p,h,s,current_target=current)
        self.assertEqual(report['freshness'],'stale')
        self.assertEqual(head,self.git('rev-parse','HEAD'))

    def test_uncommitted_contract_is_read_from_candidate_not_old_head(self):
        p,h,s=self.graph()
        p['context_management']['components'][1]['documents']=[{'path':'docs/regla.md','kind':'technical','roles':['reviewer'],'phases':['revision']}]
        changed=self.write('docs/regla.md','nueva regla todavía sin commit\n')
        result=compatibilidad.inspect(self.root,p,h,s)
        refs=[r for r in result['document_refs'] if r['path']=='docs/regla.md' and r['revision']==h['scope']['head']]
        self.assertEqual(len(refs),1)
        self.assertEqual(refs[0]['sha256'],hashlib.sha256(changed.read_bytes()).hexdigest())
        self.assertEqual(refs[0]['observation'],'worktree')

    def test_head_simulation_does_not_certify_uncommitted_functional_candidate(self):
        p,h,s=self.graph();sim=self.simulation(h,s)
        self.write('src/b.py','uncommitted incompatible behavior\n')
        first=compatibilidad.inspect(self.root,p,h,s,simulation=sim)
        result=compatibilidad.inspect(self.root,p,h,s,simulation=sim,semantic_review=self.review(first))
        self.assertNotEqual(result['outcome'],'compatible')
        self.assertEqual(result['coverage'],'partial')
        self.assertIn('SIMULATION_COVERS_HEAD_ONLY',result['limitations'])

    def test_dependency_review_can_resolve_advisory_without_erasing_impact(self):
        p,h,s=self.graph(dependent=True);sim=self.simulation(h,s)
        first=compatibilidad.inspect(self.root,p,h,s,simulation=sim)
        result=compatibilidad.inspect(self.root,p,h,s,simulation=sim,semantic_review=self.review(first))
        self.assertEqual(result['outcome'],'compatible')
        self.assertEqual(result['affected_consumers'],['consumer'])

    def test_semantic_references_obey_total_budget_and_relevant_paths(self):
        p,h,s=self.graph();first=compatibilidad.inspect(self.root,p,h,s)
        review=self.review(first,'conflict_detected',[{'type':'functional','reason':'review','owner':'reviewer',
                    'references':[{'path':'docs/regla.md','revision':s['target_sha'],'sha256':'0'*64}]}])
        with self.assertRaisesRegex(ValueError,'SEMANTIC_REFERENCE_OUTSIDE_SCOPE'):
            compatibilidad.inspect(self.root,p,h,s,semantic_review=review)

        payload=subprocess.check_output(['git','-C',str(self.root),'cat-file','blob',s['target_sha']+':src/a.py'])
        ref={'path':'src/a.py','revision':s['target_sha'],'sha256':hashlib.sha256(payload).hexdigest()}
        review['findings'][0]['references']=[ref,ref]
        p['context_management']['limits']['total_bytes']=len(payload)
        first=compatibilidad.inspect(self.root,p,h,s);review['scope_digest']=first['scope_digest']
        with self.assertRaisesRegex(ValueError,'CONTEXT_READ_LIMIT'):
            compatibilidad.inspect(self.root,p,h,s,semantic_review=review)

    def test_unknown_recommended_check_remains_pending_without_command(self):
        p,h,s=self.graph()
        self.write('docs/pruebas/policy.json',json.dumps({'checks':[],'rules':[
            {'id':'missing-consumer','paths':['src/a.py'],'checks':['absent-check'],'reason':'review needed'}]}))
        result=compatibilidad.inspect(self.root,p,h,s)
        self.assertTrue(any('UNKNOWN_RECOMMENDED_CHECK' in row['reason'] for row in result['findings']))
        self.assertEqual(result['recommended_checks'],[])
        self.assertFalse(result['combined_tests_executed'])

    def test_F_missing_or_unverifiable_target_is_not_compatible(self):
        p,h,s=self.graph()
        for status in ['missing','access_denied','connection_error','unverified']:
            other={**s,'status':status,'target_sha':None,'objects_available':False}
            result=compatibilidad.inspect(self.root,p,h,other)
            self.assertEqual(result['outcome'],'undetermined')
            self.assertEqual(result['freshness'],'unverified')

    def test_simulation_does_not_change_user_index_refs_or_worktree(self):
        p,h,s=self.graph(shared=True)
        refs=self.git('show-ref');index=(self.root/'.git/index').read_bytes();state=self.git('status','--porcelain=v1')
        result=self.simulation(h,s)
        self.assertEqual(result['status'],'conflict')
        self.assertEqual(refs,self.git('show-ref'))
        self.assertEqual(index,(self.root/'.git/index').read_bytes())
        self.assertEqual(state,self.git('status','--porcelain=v1'))

    def test_snapshot_fetches_exact_remote_ref_without_touching_heads(self):
        p,h,s=self.graph()
        remote=self.root/'remote.git'
        self.git('init','--bare',str(remote)); self.git('remote','add','origin',str(remote))
        self.git('push','origin','quality:refs/heads/quality')
        p['project']['repository']['url']=str(remote)
        schema=KIT/'docs/plantillas/git-target-snapshot.schema.json'
        self.assertTrue(schema.is_file(),'Snapshot schema missing')
        self.write('docs/plantillas/git-target-snapshot.schema.json',schema.read_text())
        heads=self.git('for-each-ref','--format=%(refname) %(objectname)','refs/heads')
        observed=entrega.snapshot(self.root,p,'HU002','1')
        self.assertEqual(observed['status'],'verified')
        self.assertEqual(observed['target_sha'],s['target_sha'])
        self.assertEqual(heads,self.git('for-each-ref','--format=%(refname) %(objectname)','refs/heads'))


if __name__=='__main__':unittest.main()
