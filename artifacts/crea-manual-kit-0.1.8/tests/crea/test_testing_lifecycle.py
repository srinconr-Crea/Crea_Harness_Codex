"""Contratos opt-in: procesos pytest reales, guardas observadas y fixtures Git."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

from test_testing_adapters import AdaptersTests as Base
from testing import workflow,catalog,attempts,schemas,reports
from testing.common import contract,digest,read,write,KIT,file_hash

class LifecycleTests(Base):
    # Do not rerun inherited historical test methods; this class adds focused fixtures.
    def fixture(self):
        base,p,e,_=self.local_setup(); policy=read(p); settings=read(e)
        shutil.copytree(KIT/'scripts/crea/testing',self.root/'scripts/crea/testing')
        shutil.copyfile(KIT/'scripts/crea/run_pytest.py',self.root/'scripts/crea/run_pytest.py')
        # The copied plugin imports no Crea runtime; constrain body inputs separately.
        policy['rules'].append({'id':'TOOLS','paths':['scripts/*'],'checks':[],'reason':'prepared local plugin'})
        policy['rules'].append({'id':'OLD_EVIDENCE','paths':['docs/hu/*'],'checks':[],'reason':'preserved previous attempts; not reused'})
        policy['lifecycle']={'schema_version':'1.0','locations':[{'path':'tests','kind':'tests'}],
            'test_inventory':[{'id':'codes','pattern':'tests/test_*.py','check_ids':['unit'],'purpose':'real code behavior','provenance':'reviewed fixture','state':'active',
                               'expected_nodeids':['tests/test_codes.py::test_valid','tests/test_codes.py::test_invalid']}]}
        policy['checks'][0]['argv']=['python','scripts/crea/run_pytest.py','-c','pytest.ini','-q','-p','no:cacheprovider','tests/test_codes.py',
            '--junitxml={junit_path}','--crea-inventory={inventory_path}']
        settings['outputs']=[]
        settings['attempt_templates']={'schema_version':'1.0','evidence_dir':'docs/hu/{change}/pruebas/attempt-{attempt}',
            'junit_path':'{evidence_dir}/junit-{check_id}.xml','inventory_path':'{evidence_dir}/inventory-{check_id}.json','coverage_path':None}
        settings['reviewed_policy_digest']=digest(policy)
        write(p,policy); write(e,settings)
        return base,p,e

    def plan(self,base,p,e,change='one',attempt='1'):
        return workflow.make_plan(self.root,p,e,base,['CA01','CA02'],change=change,attempt=attempt)

    def retain(self,label,plan=None,result=None,gate=None):
        evidence=KIT.parents[1]/'docs/hu/gestionar-ciclo-vida-pruebas-proyecto'
        import uuid
        target=evidence/'fixtures'/(label+'-'+uuid.uuid4().hex)
        if plan: write(self.root/'docs/hu/one/pruebas/attempt-1/plan.json',plan)
        if result: write(self.root/'docs/hu/one/pruebas/attempt-1/resultados.json',result)
        if gate: write(self.root/'docs/hu/one/pruebas/attempt-1/gate.json',gate)
        shutil.copytree(self.root,target)
        write(evidence/(label+'-latest.json'),{'fixture':str(target),'source_root':str(self.root)})

    def test_attempts_two_hu_unchanged_configuration_real_run_gate(self):
        base,p,e=self.fixture(); before=(file_hash(p),file_hash(e))
        with patch.object(workflow.execution,'run_process',side_effect=AssertionError('plan executed suite')) as plan_processes:
            plan=self.plan(base,p,e)
        self.assertEqual(plan['status'],'ready',plan['blockers'])
        result=workflow.run(self.root,p,e,plan)
        self.assertEqual(result['records'][0]['status'],'passed',result)
        with patch.object(workflow.execution,'run_process',side_effect=AssertionError('gate executed suite')) as gate_processes:
            self.assertEqual(workflow.gate(self.root,p,e,plan,result)['status'],'passed')
        with self.assertRaises(ValueError): workflow.run(self.root,p,e,plan)
        second=self.plan(base,p,e,'two','2')
        self.assertNotEqual(plan['plan_id'],second['plan_id'])
        self.assertEqual(before,(file_hash(p),file_hash(e)))
        result2=workflow.run(self.root,p,e,second)
        self.assertEqual(result2['records'][0]['status'],'passed',result2)
        self.assertEqual(workflow.gate(self.root,p,e,second,result)['status'],'blocked')
        self.assertEqual(workflow.gate(self.root,p,e,second,result2)['status'],'passed')
        self.retain('two-hu',plan,result,workflow.gate(self.root,p,e,plan,result))
        write(KIT.parents[1]/'docs/hu/gestionar-ciclo-vida-pruebas-proyecto/process-observations.json',
              {'plan_suite_calls':len(plan_processes.call_args_list),'gate_suite_calls':len(gate_processes.call_args_list),
               'policy_sha256_before':before[0],'policy_sha256_after':file_hash(p),'execution_sha256_before':before[1],
               'execution_sha256_after':file_hash(e),'first_plan':plan['plan_id'],'second_plan':second['plan_id']})

    def test_required_nodeid_excluded_even_same_file_other_test_passes(self):
        base,p,e=self.fixture(); policy=read(p); policy['checks'][0]['argv'].insert(-2,'-ktest_valid'); policy['checks'][0]['min_tests']=1
        policy['checks'][0]['required_assertions']=['CA01']; write(p,policy); settings=read(e); settings['reviewed_policy_digest']=digest(policy); write(e,settings)
        plan=self.plan(base,p,e); result=workflow.run(self.root,p,e,plan)
        self.assertEqual(result['records'][0]['status'],'blocked',result)
        inventory=read(self.root/'docs/hu/one/pruebas/attempt-1/inventory-unit.json')
        self.assertTrue(next(x for x in inventory['items'] if x['nodeid'].endswith('test_invalid'))['deselected'])
        self.assertEqual(workflow.gate(self.root,p,e,plan,result)['status'],'blocked')
        self.retain('missing-required',plan,result,workflow.gate(self.root,p,e,plan,result))

    def test_discover_has_no_import_or_suite_process_and_no_write(self):
        base,p,e=self.fixture(); marker=self.root/'SIDE_EFFECT'
        self.write('tests/conftest.py',f'from pathlib import Path\nPath({str(marker)!r}).write_text("imported")\nraise RuntimeError("must not import")\n')
        self.write('pyproject.toml','[tool.other]\nvalue=true\n')
        before={n:file_hash(self.root/n) for n in catalog.names(self.root)}
        with patch('subprocess.Popen',side_effect=AssertionError('subprocess forbidden')) as processes,patch('builtins.__import__',wraps=__import__) as imported:
            report=catalog.discover(self.root,read(p))
        self.assertFalse(marker.exists()); self.assertTrue(report['partial'])
        self.assertFalse(any('conftest' in str(c.args[0]) for c in imported.call_args_list))
        write(KIT.parents[1]/'docs/hu/gestionar-ciclo-vida-pruebas-proyecto/discovery-observations.json',
              {'subprocess_attempts':len(processes.call_args_list),'conftest_import_attempts':len([c for c in imported.call_args_list if 'conftest' in str(c.args[0])]),
               'side_effect_file_observed':marker.exists(),'source_files_unchanged':before=={n:file_hash(self.root/n) for n in catalog.names(self.root)}})
        self.assertEqual(before,{n:file_hash(self.root/n) for n in catalog.names(self.root)})
        self.assertTrue(any(r['path']=='tests/test_codes.py' for r in report['rows']))
        for bad in ['../escape.json','docs/hu/one/pruebas/receipt-unit.json']:
            with self.assertRaises(ValueError): catalog.save(self.root,bad,report)
        catalog.save(self.root,'docs/hu/one/handoffs/planificacion-1-inventory.json',report)
        with self.assertRaises(ValueError): catalog.save(self.root,'docs/hu/one/handoffs/planificacion-1-inventory.json',report)

    def test_criteria_selects_unchanged_and_unknown_still_blocks(self):
        base,p,e=self.fixture(); policy=read(p); policy['rules']=[]
        result=contract.build_plan(self.root,policy,[],base,['CA01'])
        self.assertIn('declared-required-criterion',result['selected'][0]['rule_ids'])
        result=contract.build_plan(self.root,policy,[{'path':'unknown.zz','status':'A'}],base,['CA01'])
        self.assertTrue(any('UNCLASSIFIED' in b for b in result['blockers']))
        result=contract.build_plan(self.root,policy,[],base,['NO_ORACLE'])
        self.assertTrue(any('CRITERION_WITHOUT_CHECK' in b for b in result['blockers']))

    def test_schema_and_retirement_historical_definition(self):
        _,p,e=self.fixture(); policy=read(p)
        for ident in ['../bad','']:
            changed=copy.deepcopy(policy); changed['lifecycle']['test_inventory'][0]['id']=ident
            with self.assertRaises(ValueError): schemas.validate('policy',changed)
        old=copy.deepcopy(policy['checks'][0]); policy['checks'][0]['configured']=False; row=policy['lifecycle']['test_inventory'][0]
        row['state']='retired'; row['retirement']={'source':'HU','reason':'feature removed','decision_ref':{'path':'decision.md','sha256':'0'*64},'replacement_ids':[], 'previous_definition':old,'previous_digest':digest(old)}
        with self.assertRaises(ValueError): contract.validate_policy(policy)
        policy['rules']=[]; contract.validate_policy(policy)
        result=contract.build_plan(self.root,policy,[],'fixture',[],required_check_ids=['unit'])
        self.assertEqual(result['status'],'blocked')
        self.assertIn('CHECK_NOT_CONFIGURED: unit',result['blockers'])

    def test_reconcile_full_git_and_changed_association_expected(self):
        base,p,e=self.fixture(); self.write('tests/test_new.py','def test_new():\n    assert 1 == 1\n')
        self.write('elsewhere/test_other.py','def test_other():\n    assert 1 == 1\n')
        policy=read(p)
        report=catalog.reconcile(self.root,policy,base)
        rows={r['path']:r for r in report['rows']}
        self.assertEqual(rows['tests/test_new.py']['check_ids'],['unit'])
        self.assertEqual(rows['elsewhere/test_other.py']['status'],'unregistered')
        plan=self.plan(base,p,e)
        self.assertIn('tests/test_new.py',plan['provenance']['test_inventory']['expected']['unit']['files'])

    def test_template_grammar_and_traversal(self):
        base,p,e=self.fixture()
        for token in ['{HOME}','--bad={junit_path}','x{change}','$(whoami)','{coverage_path}']:
            if '{' in token:
                with self.assertRaises(ValueError): attempts.expand(token,{'junit_path':'a','coverage_path':'b'})
        self.assertEqual(attempts.expand('--cov-report=json:{coverage_path}',{'coverage_path':'reports/c.json'}),'--cov-report=json:reports/c.json')
        for slug in ['../bad','x/y','x;echo']:
            with self.assertRaises(ValueError): self.plan(base,p,e,slug)

    def test_baseline_applicability_without_business_or_runtime(self):
        p={'checks':[]}
        rows=catalog.baseline(['README.md','config.json','src/a.py','job.sql','book.ipynb'],p)
        self.assertEqual({r['technology'] for r in rows},{'documents','python','sql','notebook'})
        self.assertEqual(next(r for r in rows if r['technology']=='sql')['status'],'pending_tool')
        p={'checks':[{'configured':True,'criteria':['python']}]}
        self.assertEqual(catalog.baseline(['a.py'],p)[0]['status'],'equivalent')

    def test_cli_discover_before_setup_and_reconcile(self):
        base,p,e=self.fixture(); project=read(KIT/'docs/proyecto.json')
        project['project']['setup_complete']=False
        write(self.root/'docs/proyecto.json',project)
        for action,extra in [('discover',[]),('reconcile',['--base',base])]:
            proc=subprocess.run([sys.executable,'-B',str(KIT/'scripts/crea/pruebas.py'),action,'--repo',str(self.root),'--policy','policy.json',*extra],capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stderr)
            self.assertEqual(json.loads(proc.stdout)['execution'],'not_run')
        proc=subprocess.run([sys.executable,'-B',str(KIT/'scripts/crea/pruebas.py'),'reconcile','--repo',str(self.root),'--policy','policy.json','--base','not-a-ref'],capture_output=True,text=True)
        self.assertEqual(proc.returncode,4,proc.stderr)

    def test_cli_missing_dependency_has_inspection_error_code(self):
        base,p,e=self.fixture()
        for action,extra in [('discover',[]),('reconcile',['--base',base])]:
            proc=subprocess.run([sys.executable,'-S','-B',str(KIT/'scripts/crea/pruebas.py'),action,'--repo',str(self.root),'--policy','policy.json',*extra],capture_output=True,text=True)
            self.assertEqual(proc.returncode,4,proc.stderr)
            self.assertEqual(json.loads(proc.stderr)['error'],'DEPENDENCY_UNAVAILABLE')

    def test_real_plugin_parametrization_custom_root_and_foreign_junit(self):
        self.fixture()
        self.write('qa/pytest.ini','[pytest]\n')
        self.write('qa/tests/test_custom.py','import pytest\n@pytest.mark.parametrize("x",[1,2])\ndef test_custom(x):\n    assert x > 0\n')
        proc=subprocess.run([sys.executable,'-B',str(self.root/'scripts/crea/run_pytest.py'),'-c','qa/pytest.ini','qa/tests','-p','no:cacheprovider','--junitxml=custom.xml','--crea-inventory=custom.json'],cwd=self.root,capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
        expected={'files':['qa/tests/test_custom.py'],'nodeids':['qa/tests/test_custom.py::test_custom[1]'],'complete_files':['qa/tests/test_custom.py']}
        detail=reports.inventory(self.root/'custom.json',self.root/'custom.xml',expected)
        self.assertEqual(len(detail['executed_nodeids']),2)
        changed=read(self.root/'custom.json'); changed['run_id']='0'*64; write(self.root/'custom.json',changed)
        with self.assertRaises(ValueError): reports.inventory(self.root/'custom.json',self.root/'custom.xml',expected)

    def test_real_plugin_skip_failure_setup_error_and_collection_error(self):
        self.fixture()
        for label,body in [('skip','import pytest\n@pytest.mark.skip(reason="reviewed skip")\ndef test_x():\n    assert False\n'),
                           ('fail','def test_x():\n    assert False\n'),
                           ('setup','import pytest\n@pytest.fixture\ndef broken():\n    raise ValueError("fixture failed")\ndef test_x(broken):\n    assert True\n'),
                           ('collection','raise RuntimeError("collection failed")\n')]:
            self.write('cases/test_'+label+'.py',body)
            proc=subprocess.run([sys.executable,'-B',str(self.root/'scripts/crea/run_pytest.py'),'-c','pytest.ini','cases/test_'+label+'.py','-p','no:cacheprovider','--junitxml='+label+'.xml','--crea-inventory='+label+'.json'],cwd=self.root,capture_output=True,text=True)
            data=read(self.root/(label+'.json'))
            if label=='collection': self.assertTrue(data['collection_errors'])
            else:
                phases=data['items'][0]['phases']
                self.assertTrue('failed' in phases.values() or 'skipped' in phases.values())
            with self.assertRaises(ValueError): reports.inventory(self.root/(label+'.json'),self.root/(label+'.xml'),{'files':['cases/test_'+label+'.py'],'nodeids':[],'complete_files':[]})

    def test_materialized_baseline_real_execution_and_no_empty_suite(self):
        self.fixture(); self.write('config.json','{"enabled":true}'); self.write('plain.py','x=1\n')
        result=catalog.materialize_baseline(self.root,['config.json','plain.py'],'tests/proyecto/test_validaciones_tecnicas.py')
        self.assertEqual(result['status'],'materialized_not_run')
        proc=subprocess.run([sys.executable,'-B','-m','pytest','-c','pytest.ini','-q','-p','no:cacheprovider',result['path']],cwd=self.root,capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
        self.assertFalse(catalog.materialize_baseline(self.root,[],'tests/empty.py')['written'])
        self.assertFalse(catalog.materialize_baseline(self.root,['plain.py'],'tests/existing.py',equivalent=True)['written'])

    def test_attempt_occupied_report_rejected_before_plan_and_source_change_invalidates(self):
        base,p,e=self.fixture()
        self.write('docs/hu/one/pruebas/attempt-1/junit-unit.xml','old bytes')
        with self.assertRaisesRegex(ValueError,'ATTEMPT_ALREADY_EXISTS'): self.plan(base,p,e)
        self.assertEqual((self.root/'docs/hu/one/pruebas/attempt-1/junit-unit.xml').read_text(),'old bytes')
        plan=self.plan(base,p,e,'fresh')
        settings=read(e); settings['max_evidence_age_seconds']=60; write(e,settings)
        with self.assertRaises(ValueError): workflow.run(self.root,p,e,plan)

    def test_inventory_expectations_are_functional_handoff_context(self):
        import test_transiciones
        h=test_transiciones.handoff()
        expected={'unit':{'files':['tests/test_codes.py'],'nodeids':['tests/test_codes.py::test_invalid'],'complete_files':[]}}
        h['evidence']['test_inventory_review']={'schema_version':'1.0','expected':expected,'reconciled':True,'affected':[],'dispositions':[],'inclusion_ref':None}
        schemas.validate_schema(read(KIT/'docs/plantillas/handoff.schema.json'),h)
        before=workflow.git_adapter.handoff_context(h)
        h['evidence']['test_inventory_review']['expected']['unit']['nodeids']=[]
        self.assertNotEqual(before,workflow.git_adapter.handoff_context(h))
        h['evidence'].pop('test_inventory_review')
        self.assertNotEqual(before,workflow.git_adapter.handoff_context(h))

    def test_transition_conditions_informative_promoted_and_dependency_error(self):
        import test_transiciones
        import transiciones
        base,p,e=self.fixture(); self.write('criteria.md','CA01'); self.write('validation.md','review')
        project=read(KIT/'docs/proyecto.json'); project['project']['setup_complete']=True
        project.pop('context_management',None)
        project['validation']['testing']['policy_path']='policy.json'; project['validation']['testing']['execution_path']='execution.json'
        write(self.root/'docs/proyecto.json',project)
        h=test_transiciones.handoff(); h['scope']['base']=base
        name='docs/hu/synthetic/handoffs/planificacion-1.json'; write(self.root/name,h)
        report=transiciones.check(self.root,name,'to_apply')
        self.assertEqual(report['exit_code'],3,report)
        self.assertTrue(any(f['condition_id']=='TEST_INVENTORY_RECONCILED' for f in report['findings']))
        self.assertIn('APPLY_AUTHORIZATION_MISSING',report['existing_constraints'])
        h['continuation']['transition']='to_test'; write(self.root/name,h)
        self.assertEqual(transiciones.check(self.root,name,'to_test')['exit_code'],0)
        self.write('promotion.md','reviewed condition promotion')
        project['workflow']['transitions']={'mode':'enforcing','blocking_conditions':['TEST_INVENTORY_RECONCILED'],'promotion_ref':'promotion.md'}
        write(self.root/'docs/proyecto.json',project)
        self.assertEqual(transiciones.check(self.root,name,'to_test')['exit_code'],2)
        with patch.object(catalog,'review',side_effect=ImportError('missing dependency')):
            report=transiciones.check(self.root,name,'to_test')
        self.assertEqual(report['exit_code'],4)

    def test_reconcile_does_not_read_unaffected_suite_body_and_tracks_rename_delete(self):
        base,p,e=self.fixture()
        self.write('tests/test_untouched.py','def test_old():\n    assert 2 > 1\n')
        self.git('add','--','tests/test_untouched.py'); self.git('commit','-m','fixture untouched suite')
        self.git('mv','tests/test_untouched.py','tests/test_moved.py')
        read_bytes=Path.read_bytes
        def guard(path):
            if path.name=='test_codes.py': raise AssertionError('unaffected body read')
            return read_bytes(path)
        # Commit all currently untracked inputs so only rename belongs to the diff.
        self.git('add','--','src','tests/test_codes.py','pytest.ini','policy.json','execution.json','scripts')
        self.git('commit','-m','prepared fixture')
        head=self.git('rev-parse','HEAD'); self.git('mv','tests/test_moved.py','tests/test_renamed.py')
        with patch.object(Path,'read_bytes',guard): report=catalog.reconcile(self.root,read(p),head)
        self.assertTrue(any(r.get('old_path')=='tests/test_moved.py' and r['status']=='moved' for r in report['rows']))

    def test_resolved_content_commit_keeps_gate_and_expected_metadata_invalidates(self):
        import test_transiciones
        base,p,e=self.fixture()
        project=read(KIT/'docs/proyecto.json'); project['project']['setup_complete']=True
        project['validation']['testing']['policy_path']='policy.json'; project['validation']['testing']['execution_path']='execution.json'
        # Context remains optional; this fixture includes the same logical projection.
        project.pop('context_management',None); write(self.root/'docs/proyecto.json',project)
        h=test_transiciones.handoff(); h['identity']['change']='one'; h['scope']['git_inputs']={'unit':[]}; h['scope']['base']=base
        h['evidence']['test_inventory_review']={'schema_version':'1.0','expected':{'unit':{'files':[],'nodeids':['tests/test_codes.py::test_invalid'],'complete_files':[]}},'reconciled':True,'affected':['tests/test_codes.py'],'dispositions':[],'inclusion_ref':None}
        write(self.root/'docs/hu/one/handoffs/planificacion-1.json',h)
        self.write('criteria.md','CA01'); self.write('validation.md','review')
        policy=read(p); policy['rules'].append({'id':'DOCS','paths':['criteria.md','validation.md'],'checks':[],'reason':'references'}); write(p,policy)
        settings=read(e); settings['reviewed_policy_digest']=digest(policy); write(e,settings)
        plan=self.plan(base,p,e); result=workflow.run(self.root,p,e,plan)
        self.assertEqual(result['records'][0]['status'],'passed',result)
        self.git('add','--','.'); self.git('commit','-m','synthetic tested tree')
        resolved_policy,resolved=workflow.resolved_settings(self.root,p,e,plan)
        view=workflow.git_adapter.content_view(self.root,base,resolved['outputs'],plan['provenance']['projection'],[pat for c in resolved_policy['checks'] for pat in c['inputs']])
        self.assertTrue(workflow.git_adapter.verify_commit(self.root,base,'HEAD',view,['*']))
        with patch.object(workflow.execution,'run_process',side_effect=AssertionError('Reviewer reran suite')):
            self.assertEqual(workflow.gate(self.root,p,e,plan,result)['status'],'passed')
        h['identity']['attempt']=2; h['previous_handoff']={'path':'docs/hu/one/handoffs/planificacion-1.json','sha256':file_hash(self.root/'docs/hu/one/handoffs/planificacion-1.json')}
        h['evidence']['test_inventory_review']['expected']['unit']['nodeids']=[]
        write(self.root/'docs/hu/one/handoffs/planificacion-2.json',h)
        self.assertEqual(workflow.gate(self.root,p,e,plan,result)['status'],'blocked')

    def test_archived_retirement_reference_keeps_gate_and_tamper_blocks(self):
        base,p,e=self.fixture(); policy=read(p)
        old=copy.deepcopy(policy['checks'][0]); old['id']='historical'
        source='openspec/changes/old/design.md'; target='openspec/changes/archive/old/design.md'
        self.write(source,'Reviewed retirement of obsolete feature\n')
        sha=file_hash(self.root/source)
        policy['lifecycle']['test_inventory'].append({'id':'retired','pattern':'tests/test_old.py','check_ids':['historical'],
            'purpose':'removed feature','provenance':'historical','state':'retired','retirement':{'source':'HU old','reason':'feature removed',
            'decision_ref':{'path':source,'sha256':sha},'replacement_ids':[],'previous_definition':old,'previous_digest':digest(old)}})
        policy['rules'].append({'id':'ARCHIVE','paths':['openspec/*'],'checks':[],'reason':'exact reviewed movement'})
        write(p,policy); settings=read(e); settings['reviewed_policy_digest']=digest(policy); write(e,settings)
        projection={'version':'content-v2','change':'one','context':{},'history':{},'moves':[{'from':source,'to':target,'sha256':sha}], 'sync':[],'git_inputs':{'unit':[]}}
        plan=workflow.make_plan(self.root,p,e,base,['CA01','CA02'],projection=projection,change='one',attempt='1')
        result=workflow.run(self.root,p,e,plan); self.assertEqual(result['records'][0]['status'],'passed',result)
        (self.root/target).parent.mkdir(parents=True,exist_ok=True); (self.root/source).replace(self.root/target)
        with patch.object(workflow.execution,'run_process',side_effect=AssertionError('archive reran suite')):
            self.assertEqual(workflow.gate(self.root,p,e,plan,result)['status'],'passed')
        self.write(target,'tampered retirement decision')
        self.assertEqual(workflow.gate(self.root,p,e,plan,result)['status'],'blocked')

    def test_explicit_pytest_entry_identity_invalidates_existing_plan(self):
        base,p,e=self.fixture(); plan=self.plan(base,p,e)
        original=workflow.file_hash
        def changed(path,*args,**kwargs):
            return '0'*64 if Path(path)==KIT/'scripts/crea/run_pytest.py' else original(path,*args,**kwargs)
        with patch.object(workflow,'file_hash',side_effect=changed):
            self.assertFalse(workflow.current(self.root,p,e,plan))

    def test_deleted_active_test_requires_retirement_review_and_unrelated_history_does_not(self):
        import test_transiciones
        import transiciones
        base,p,e=self.fixture(); self.git('add','--','tests/test_codes.py'); self.git('commit','-m','tracked test to retire')
        head=self.git('rev-parse','HEAD'); (self.root/'tests/test_codes.py').unlink()
        self.write('criteria.md','CA01'); self.write('validation.md','review')
        h=test_transiciones.handoff(); h['scope']['base']=head; h['continuation']['transition']='to_test'
        h['evidence']['test_inventory_review']={'schema_version':'1.0','expected':{},'reconciled':True,'affected':['tests/test_codes.py'],'dispositions':[],'inclusion_ref':None}
        findings=catalog.review(self.root,read(p),h)
        self.assertTrue(any(f['condition_id']=='TEST_RETIREMENT_REVIEWED' for f in findings))
        project=read(KIT/'docs/proyecto.json'); project.pop('context_management',None); project['project']['setup_complete']=True
        project['validation']['testing']['policy_path']='policy.json'; project['validation']['testing']['execution_path']='execution.json'
        self.write('promotion.md','Reviewer promotion of retirement condition')
        project['workflow']['transitions']={'mode':'enforcing','blocking_conditions':['TEST_RETIREMENT_REVIEWED'],'promotion_ref':'promotion.md'}
        write(self.root/'docs/proyecto.json',project)
        name='docs/hu/synthetic/handoffs/planificacion-1.json'; write(self.root/name,h)
        self.assertEqual(transiciones.check(self.root,name,'to_test')['exit_code'],2)
        self.write('retirement.md','Reviewer approved feature removal and consumers')
        ref={'path':'retirement.md','sha256':file_hash(self.root/'retirement.md')}
        h['evidence']['test_inventory_review']['dispositions']=[{'id':'codes','action':'retire','reason':'removed feature reviewed','decision_ref':ref}]
        policy=read(p); old=copy.deepcopy(policy['checks'][0]); old['id']='historic'
        policy['lifecycle']['test_inventory'].append({'id':'historic','pattern':'tests/test_historic.py','check_ids':['historic'],'purpose':'past retirement','provenance':'previous HU','state':'retired',
            'retirement':{'source':'past HU','reason':'old feature removed','decision_ref':ref,'replacement_ids':[],'previous_definition':old,'previous_digest':digest(old)}})
        self.assertFalse(any(f['condition_id']=='TEST_RETIREMENT_REVIEWED' for f in catalog.review(self.root,policy,h)))

# Base helpers retained without inheriting/recollecting the historic suite.
for _name in list(vars(Base)):
    if _name.startswith('test_') and _name not in vars(LifecycleTests): setattr(LifecycleTests,_name,None)
del Base

if __name__=='__main__': unittest.main()
