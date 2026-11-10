"""Una observación tardía no oculta cambios funcionales ni muta content-v2."""
import copy
import json
import unittest

import test_testing_adapters as legacy
from testing import git_adapter, workflow
from testing.common import KIT, file_hash, read, write, digest


class ContentV3Tests(unittest.TestCase):
    setUp=legacy.AdaptersTests.setUp
    cleanup=legacy.AdaptersTests.cleanup
    write=legacy.AdaptersTests.write
    git=legacy.AdaptersTests.git
    init_git=legacy.AdaptersTests.init_git
    local_setup=legacy.AdaptersTests.local_setup

    def test_real_plan_run_gate_remains_current_after_declared_observation(self):
        base,policy,execution,_=self.local_setup()
        name='docs/hu/synthetic/compatibilidad/attempt-1/simulation.json'
        self.write('docs/plantillas/compatibilidad-simulation.schema.json',(KIT/'docs/plantillas/compatibilidad-simulation.schema.json').read_text())
        self.git('add','--','docs/plantillas');self.git('commit','-m','reviewed schemas')
        base=self.git('rev-parse','HEAD')
        p={'version':'content-v3','change':'synthetic','context':{},'moves':[],'sync':[],
           'git_inputs':{'unit':[]},'compatibility_artifacts':[{'path':name,'kind':'git_integration_simulation'}]}
        plan=workflow.make_plan(self.root,policy,execution,base,['CA01','CA02'],projection=p)
        self.assertEqual(plan['status'],'ready',plan['blockers'])
        result=workflow.run(self.root,policy,execution,plan)
        self.assertEqual(workflow.gate(self.root,policy,execution,plan,result)['status'],'passed')
        self.write(name,json.dumps({'schema_version':'1.0','kind':'git_integration_simulation','change':'synthetic',
                   'source_sha':base,'target_sha':base,'status':'clean','conflict_paths':[],
                   'limits':[],'combined_tests_executed':False}))
        self.assertTrue(workflow.current(self.root,policy,execution,plan))
        self.assertEqual(workflow.gate(self.root,policy,execution,plan,result)['status'],'passed')
        self.write('src/codes.py','def code(value): return "incorrect"\n')
        self.assertEqual(workflow.gate(self.root,policy,execution,plan,result)['status'],'blocked')

    def fixture(self):
        self.init_git()
        self.write('docs/plantillas/compatibilidad-simulation.schema.json',(KIT/'docs/plantillas/compatibilidad-simulation.schema.json').read_text())
        self.write('src/value.py','value = 1\n')
        self.git('add','--','docs/plantillas','src');self.git('commit','-m','baseline')
        base=self.git('rev-parse','HEAD')
        name='docs/hu/synthetic/compatibilidad/attempt-1/simulation.json'
        p={'version':'content-v3','change':'synthetic','context':{},'moves':[],'sync':[],
           'git_inputs':{},'history':{},'compatibility_artifacts':[{'path':name,'kind':'git_integration_simulation'}]}
        data={'schema_version':'1.0','kind':'git_integration_simulation','change':'synthetic',
              'source_sha':base,'target_sha':base,'status':'clean','conflict_paths':[],
              'limits':[],'combined_tests_executed':False}
        return base,name,p,data

    def test_exact_late_observation_preserves_identity_but_code_does_not(self):
        base,name,p,data=self.fixture()
        before=git_adapter.content_view(self.root,base,[],p)['input_digest']
        self.write(name,json.dumps(data))
        self.assertEqual(before,git_adapter.content_view(self.root,base,[],p)['input_digest'])
        self.write('src/value.py','value = 2\n')
        self.assertNotEqual(before,git_adapter.content_view(self.root,base,[],p)['input_digest'])

    def test_legacy_view_keeps_new_observation_as_functional_input(self):
        base,name,p,data=self.fixture();p['version']='content-v2'
        before=git_adapter.content_view(self.root,base,[],p)['input_digest']
        self.write(name,json.dumps(data))
        self.assertNotEqual(before,git_adapter.content_view(self.root,base,[],p)['input_digest'])

    def test_malformed_or_historical_observation_cannot_be_hidden(self):
        base,name,p,data=self.fixture()
        self.write(name,json.dumps({**data,'production_code':'unauthorized behavior'}))
        with self.assertRaises(ValueError):git_adapter.content_view(self.root,base,[],p)
        self.write(name,json.dumps(data));p['history'][name]=file_hash(self.root/name)
        self.write(name,json.dumps({**data,'status':'conflict'}))
        with self.assertRaises(ValueError):git_adapter.content_view(self.root,base,[],p)


if __name__=='__main__':unittest.main()
