"""Límites de historia, mapeo, lecturas y exportación con Git local."""
import hashlib
import subprocess
import unittest
from unittest.mock import patch
import test_target_compatibility as fixtures
import compatibilidad
import entrega
from contexto import consumer_impact
from team_common import hu_export


class BoundaryCasesTests(unittest.TestCase):
    setUp=fixtures.TargetCompatibilityTests.setUp
    cleanup=fixtures.TargetCompatibilityTests.cleanup
    write=fixtures.TargetCompatibilityTests.write
    git=fixtures.TargetCompatibilityTests.git
    init_git=fixtures.TargetCompatibilityTests.init_git
    graph=fixtures.TargetCompatibilityTests.graph
    simulation=fixtures.TargetCompatibilityTests.simulation
    review=fixtures.TargetCompatibilityTests.review

    def test_cyclic_reverse_graph_is_stable_and_disabled_mapping_is_unknown(self):
        p,h,s=self.graph(dependent=True)
        p['context_management']['components'][0]['dependencies']=['consumer']
        first=consumer_impact(p,['src/a.py'],['src/b.py'])
        self.assertEqual(first['affected_consumers'],['consumer'])
        self.assertEqual(first,consumer_impact(p,['src/a.py'],['src/b.py']))
        p['context_management']['enabled']=False
        result=compatibilidad.inspect(self.root,p,h,s)
        self.assertFalse(result['impact']['known']);self.assertEqual(result['coverage'],'partial')
        self.assertNotEqual(result['outcome'],'compatible')
        self.assertFalse(p['context_management']['enabled'])

    def test_known_text_conflict_survives_missing_mapping_and_modify_delete(self):
        p,h,s=self.graph(shared=True)
        self.git('rm','--','src/a.py');self.git('commit','-m','delete producer on feature')
        h['scope']['head']=self.git('rev-parse','HEAD')
        p['context_management']['enabled']=False
        sim=self.simulation(h,s)
        self.assertEqual(sim['status'],'conflict')
        result=compatibilidad.inspect(self.root,p,h,s,simulation=sim)
        self.assertEqual(result['outcome'],'conflict_detected')
        self.assertEqual(result['coverage'],'partial')

    def test_unavailable_merge_tree_is_honest_and_never_falls_back_to_merge(self):
        p,h,s=self.graph();original=compatibilidad.process;calls=[]
        def process(argv,**kwargs):
            calls.append(argv)
            if 'merge-tree' in argv:return subprocess.CompletedProcess(argv,129,b'',b'unsupported')
            return original(argv,**kwargs)
        with patch.object(compatibilidad,'process',side_effect=process):sim=self.simulation(h,s)
        self.assertEqual(sim['status'],'undetermined')
        self.assertFalse(any(word in args for args in calls for word in ['merge','rebase','cherry-pick']))
        result=compatibilidad.inspect(self.root,p,h,s,simulation=sim)
        self.assertNotEqual(result['outcome'],'compatible')

    def test_unrelated_or_incomplete_history_never_gets_an_invented_base(self):
        p,h,s=self.graph()
        real=entrega.git
        for mode in ['missing','multiple','shallow']:
            def observed(root,*args):
                if args[:2]==('merge-base','--all'):
                    if mode=='multiple':return h['scope']['base']+'\n'+s['target_sha']
                    raise ValueError('GIT_OPERATION_FAILED: merge-base')
                return real(root,*args)
            with self.subTest(mode=mode),patch.object(entrega,'git',side_effect=observed):
                report=compatibilidad.inspect(self.root,p,h,s)
                self.assertEqual(report['outcome'],'undetermined')
                self.assertEqual(report['coverage'],'partial')

    def test_excluded_contract_stays_in_git_scope_without_reading_its_bytes(self):
        p,h,s=self.graph()
        p['context_management']['components'][1]['documents']=[{'path':'docs/regla.md','kind':'technical','roles':['reviewer'],'phases':['revision']}]
        p['inventory']['exclude_from_context'].append('docs/regla.md')
        self.write('docs/regla.md','private content must remain unread\n')
        original=compatibilidad.worktree_document
        with patch.object(compatibilidad,'worktree_document',wraps=original):
            report=compatibilidad.inspect(self.root,p,h,s)
        self.assertIn('docs/regla.md',report['review_paths'])
        self.assertFalse(any(r['path']=='docs/regla.md' for r in report['document_refs']))
        self.assertTrue(any(isinstance(x,dict) and x.get('reason')=='CONTEXT_PATH_EXCLUDED' for x in report['limitations']))

    def test_export_is_new_exact_hu_path_and_never_overwrites_primary_evidence(self):
        self.init_git();name='docs/hu/one/compatibilidad/attempt-1/report.json'
        first=hu_export(self.root,name,{'test':True},'one');before=(self.root/name).read_bytes()
        with self.assertRaises(ValueError):hu_export(self.root,name,{'test':False},'one')
        self.assertEqual(before,(self.root/name).read_bytes())
        for bad in ['docs/hu/other/compatibilidad/report.json','../escape.json','docs/hu/one/compatibilidad/../../pruebas/receipt.json']:
            with self.subTest(path=bad),self.assertRaises(ValueError):hu_export(self.root,bad,{},'one')


if __name__=='__main__':unittest.main()
