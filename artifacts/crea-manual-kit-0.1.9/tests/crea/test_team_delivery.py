"""Entrega de equipo: refs y alcance Git reales, sin servicio remoto."""
import copy
import json
from pathlib import Path
import sys
import unittest

import test_testing_adapters as legacy
from testing.common import KIT, read, file_hash

try:
    import entrega
except ImportError:
    entrega = None


class TeamDeliveryTests(unittest.TestCase):
    setUp = legacy.AdaptersTests.setUp
    cleanup = legacy.AdaptersTests.cleanup
    write = legacy.AdaptersTests.write
    git = legacy.AdaptersTests.git
    init_git = legacy.AdaptersTests.init_git

    def config(self):
        value = read(KIT / 'docs/proyecto.json')
        value['project']['base_branch'] = 'fixture-base'
        return value

    def test_independent_target_and_legacy_fallback(self):
        self.assertIsNotNone(entrega, 'Delivery resolver is missing')
        p = self.config()
        self.assertEqual(entrega.resolve(p)['target_branch'], 'fixture-base')
        p['delivery']['pr_target_branch'] = 'quality'
        self.assertEqual(entrega.resolve(p)['target_branch'], 'quality')
        self.assertEqual(entrega.resolve(p)['base_branch'], 'fixture-base')
        p['delivery']['pr_target_branch'] = None
        self.assertEqual(entrega.resolve(p)['target_branch'], 'fixture-base')

    def test_invalid_target_does_not_silently_fall_back(self):
        p=self.config()
        for value in ['',False,4,'bad..branch','--option']:
            p['delivery']['pr_target_branch']=value
            with self.subTest(value=value),self.assertRaises(ValueError):entrega.resolve(p)

    def test_equivalent_azure_remote_forms_and_nested_remote_name(self):
        expected=('azure','org','proj','repo')
        for value in ['https://dev.azure.com/org/proj/_git/repo','https://org@dev.azure.com/org/proj/_git/repo',
                      'https://org.visualstudio.com/proj/_git/repo','git@ssh.dev.azure.com:v3/org/proj/repo']:
            with self.subTest(value=value):self.assertEqual(entrega.repository_key(value),expected)
        p=self.config();p['delivery']['remote']='team/origin'
        self.assertEqual(entrega.resolve(p)['remote'],'team/origin')

    def test_protected_and_invalid_feature_names_are_rejected(self):
        self.assertIsNotNone(entrega)
        p = self.config(); p['delivery']['pr_target_branch'] = 'quality'
        for name in ['quality', 'test', 'fixture-base', 'main', '../bad', '-option', 'feature/x\nother']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                entrega.validate_feature(p, name)
        self.assertEqual(entrega.validate_feature(p, 'feature/HU001'), 'feature/HU001')

    def test_inherited_work_is_not_attributed_to_story(self):
        self.assertIsNotNone(entrega)
        base = self.init_git(); self.git('branch', 'quality')
        self.write('sprint.txt', 'outside this story\n')
        self.git('add', '--', 'sprint.txt'); self.git('commit', '-m', 'sprint work')
        birth = self.git('rev-parse', 'HEAD')
        self.git('switch', '-c', 'feature/HU002')
        self.write('story.txt', 'own story\n')
        self.git('add', '--', 'story.txt'); self.git('commit', '-m', 'own story')
        result = entrega.ranges(self.root, birth, 'HEAD', base)
        self.assertEqual([r['path'] for r in result['story_changes']], ['story.txt'])
        self.assertEqual([r['path'] for r in result['inherited_changes']], ['sprint.txt'])
        self.assertEqual(len(result['inherited_commits']), 1)

    def test_local_check_preserves_checkout_and_detects_wrong_branch(self):
        self.assertIsNotNone(entrega)
        base = self.init_git(); self.git('switch', '-c', 'feature/HU001')
        p = self.config()
        p['delivery']['pr_target_branch'] = 'quality'
        self.git('remote', 'add', 'origin', str(self.root / 'not-contacted.git'))
        p['project']['repository']['url'] = str(self.root / 'not-contacted.git')
        before = self.git('status', '--porcelain=v1')
        result = entrega.inspect_local(self.root, p, 'feature/HU002')
        self.assertIn('CURRENT_BRANCH_MISMATCH', result['issues'])
        self.assertEqual(before, self.git('status', '--porcelain=v1'))
        self.assertEqual(base, self.git('rev-parse', 'HEAD'))

    def test_independent_target_requires_verified_scope_even_without_compatibility(self):
        self.assertTrue(hasattr(entrega,'check_scope'),'Delivery scope consumer is missing')
        q=self.init_git();self.git('branch','quality')
        self.write('sprint.txt','previous sprint work\n');self.git('add','--','sprint.txt');self.git('commit','-m','sprint')
        birth=self.git('rev-parse','HEAD');self.git('switch','-c','feature/HU002')
        self.write('own.txt','story\n');self.git('add','--','own.txt');self.git('commit','-m','story')
        p=self.config();p['delivery']['pr_target_branch']='quality';p['delivery']['compatibility']={'enabled':False}
        p['project']['repository']['url']=str(self.root)
        self.git('remote','add','origin',str(self.root))
        h={'identity':{'change':'HU002'},'scope':{'git_delivery':{'base_branch':'fixture-base',
            'source_branch':'feature/HU002','remote':'origin','branch_start_sha':birth}},'evidence':{}}
        missing=entrega.check_scope(self.root,p,h)
        self.assertIn('DELIVERY_SCOPE_SNAPSHOT_REQUIRED',missing['issues'])
        snap={'schema_version':'1.0','kind':'git_target_snapshot','change':'HU002','attempt':'1',
              'repository':list(entrega.repository_key(str(self.root))),'remote':'origin','base_branch':'fixture-base',
              'target_branch':'quality','target_sha':q,'status':'verified','objects_available':True,
              'observed_at':'2026-11-10T12:00:00Z','git_version':'git version fixture','limits':[]}
        name='docs/hu/HU002/compatibilidad/attempt-1/target.json';self.write(name,json.dumps(snap))
        h['evidence']['target_snapshot']={'path':name,'sha256':file_hash(self.root/name)}
        before=entrega.check_scope(self.root,p,h)
        self.assertIn('INHERITED_DELIVERY_SCOPE_REQUIRES_DECISION',before['issues'])
        h['scope']['git_delivery']['approved_inherited_commits']=before['ranges']['inherited_commits']
        self.assertEqual(entrega.check_scope(self.root,p,h)['issues'],[])


if __name__ == '__main__':
    unittest.main()
