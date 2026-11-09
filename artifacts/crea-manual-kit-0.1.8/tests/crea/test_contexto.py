"""Contexto proporcional: repositorios Git sintéticos, sin red."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import test_testing_adapters as legacy
from testing import git_adapter, schemas, workflow
from testing.common import KIT, read, digest, file_hash
from test_transiciones import handoff
import transiciones

MODULE = KIT / 'scripts/crea/contexto.py'
if MODULE.exists():
    import contexto
else:
    contexto = None


def document(path, **kwargs):
    return dict(path=path, kind='technical', roles=['planner','developer','tester','reviewer','principal'], phases=['planificacion','implementacion','pruebas','revision','cierre','entrega'], **kwargs)


def policy():
    return {'enabled':True,'schema_version':'1.0','components':[
        {'id':'app','paths':['src/*','old name.txt','new name.txt','deleted.txt'],'dependencies':['shared'],'documents':[document('docs/app.md')]},
        {'id':'shared','paths':['shared/*'],'dependencies':['app'],'documents':[document('docs/shared.md')]},
        {'id':'unrelated','paths':['other/*'],'dependencies':[],'documents':[document('docs/unrelated.md')]}],
        'impact_rules':[{'id':'paths','components':['app'],'paths':[],'triggers':['path_change','behavior'],'documents':['docs/app.md'],'reason':'Conservar referencias del componente','owner':'developer'}],
        'limits':{'per_document_bytes':262144,'total_bytes':2097152}}


class ContextTests(unittest.TestCase):
    setUp=legacy.AdaptersTests.setUp
    cleanup=legacy.AdaptersTests.cleanup
    write=legacy.AdaptersTests.write
    git=legacy.AdaptersTests.git
    init_git=legacy.AdaptersTests.init_git

    def setup_context(self):
        self.assertIsNotNone(contexto, 'helper de contexto no implementado')
        self.base=self.init_git()
        self.project=read(KIT/'docs/proyecto.json'); self.project['context_management']=policy()
        self.write('docs/proyecto.json',json.dumps(self.project))
        for name in ('app','shared','unrelated'):
            self.write('docs/'+name+'.md','Contenido manual '+name+'\n')
        self.write('src/main.py','value=1\n')

    def inspect(self, **kw):
        return contexto.inspect(self.root,self.project,'synthetic','developer','implementacion',self.base,**kw)

    def test_selection_is_stable_cyclic_dependencies_and_only_selected_reads(self):
        self.setup_context()
        calls=[]; original=Path.open
        def watch(path,*args,**kwargs):
            calls.append(path.relative_to(self.root).as_posix()); return original(path,*args,**kwargs)
        with patch.object(Path,'open',watch):
            first=self.inspect(); second=self.inspect()
        self.assertEqual(first['semantic'],second['semantic'])
        self.assertEqual(first['semantic']['components'],['app','shared'])
        self.assertEqual(set(calls),{'docs/app.md','docs/shared.md'})
        self.assertEqual(first['metrics']['files_read'],2)
        self.assertEqual(first['metrics']['suite_processes'],0)
        self.assertEqual(first['metrics']['remote_processes'],0)
        self.assertEqual(first['semantic']['rules'],[])

    def test_full_path_observation_retains_rename_delete_secret_and_unknown(self):
        self.setup_context()
        self.git('mv','old name.txt','new name.txt'); self.git('rm','deleted.txt')
        self.write('.env','DO_NOT_READ'); self.write('new/component.py','unknown')
        r=self.inspect()
        self.assertIn('.env',r['observation']['paths'])
        self.assertTrue({'old name.txt','new name.txt','deleted.txt'} <= set(r['observation']['paths']))
        self.assertIn('new/component.py',r['semantic']['unknown_paths'])
        self.assertEqual([x['path'] for x in r['semantic']['impact']],['docs/app.md'])

    def test_excluded_external_link_history_and_byte_limits_do_not_read_content(self):
        self.setup_context()
        p=self.project['context_management']; docs=p['components'][0]['documents']
        docs += [document('.env'),document('../outside'),document('openspec/changes/archive/old/spec.md')]
        self.write('.env','secret'); self.write('openspec/changes/archive/old/spec.md','history')
        p['limits']={'per_document_bytes':2,'total_bytes':4}
        r=self.inspect()
        self.assertEqual(r['metrics']['files_read'],0)
        self.assertTrue(r['semantic']['partial'])
        self.assertTrue(any(x['reason']=='excluded' for x in r['semantic']['omitted']))
        self.assertTrue(any(x['reason']=='unsafe_path' for x in r['semantic']['omitted']))
        self.assertTrue(any(x['reason']=='history_not_explicit' for x in r['semantic']['omitted']))

    def test_logical_selection_has_no_future_hashes_and_rows_are_reconciled(self):
        self.setup_context(); r=self.inspect()
        logical=contexto.logical(self.project,['app'],['behavior'])
        self.assertNotIn('sha256',json.dumps(logical))
        h=handoff(); h['context']['management']=logical
        review=contexto.review(r,'planned',[],null_reason='No cambio adicional previsto')
        h['evidence']['context_review']=review
        schemas.validate_schema(read(KIT/'docs/plantillas/handoff.schema.json'),h)
        self.assertEqual(contexto.check(self.root,self.project,h,r)['findings'],[])
        h['evidence']['context_review']=contexto.review(r,'final',[])
        self.assertTrue(contexto.check(self.root,self.project,h,r)['findings'])
        rows=[dict(r['semantic']['impact'][0],operation='keep',status='unchanged_justified',justification='El contrato descrito conserva su significado',references=[])]
        h['evidence']['context_review']=contexto.review(r,'final',rows)
        self.assertEqual(contexto.check(self.root,self.project,h,r)['findings'],[])
        self.project['context_management']['components'][0]['paths'].append('new/*')
        with self.assertRaisesRegex(ValueError,'OBSERVATION_IDENTITY'):
            contexto.check(self.root,self.project,h,r)

    def test_optional_schema_is_strict_and_observations_are_not_current_refs(self):
        self.setup_context(); schemas.validate('project',self.project)
        bad=copy.deepcopy(self.project); bad['context_management']['limits']['total_bytes']=0
        with self.assertRaises(ValueError): schemas.validate('project',bad)
        legacy_config=copy.deepcopy(self.project); legacy_config.pop('context_management')
        schemas.validate('project',legacy_config)
        h=handoff(); h['context']['management']=contexto.logical(self.project,['app'],[])
        r=self.inspect(); h['evidence']['context_review']=contexto.review(r,'planned',[],'Sin cambios documentales')
        before=git_adapter.handoff_context(h)
        self.write('docs/app.md','Edicion documental autorizada\n')
        h['evidence']['context_review']=contexto.review(self.inspect(),'final',[])
        self.assertEqual(before,git_adapter.handoff_context(h))
        h['context']['management']['components'].append('unrelated')
        self.assertNotEqual(before,git_adapter.handoff_context(h))

    def test_auxiliary_output_is_exclusive_and_never_implicitly_metadata(self):
        self.setup_context(); r=self.inspect()
        output='docs/hu/synthetic/contexto/implementacion-1.json'
        contexto.save(self.root,output,r,'synthetic')
        with self.assertRaises(ValueError): contexto.save(self.root,output,r,'synthetic')
        with self.assertRaises(ValueError): contexto.save(self.root,'docs/app.md',r,'synthetic')
        p={'version':'content-v2','change':'synthetic','context':{},'moves':[],'sync':[],'git_inputs':{}}
        self.assertFalse(git_adapter.managed(self.root,output,p))

    def test_error_and_promoted_context_condition_preserve_prior_controls(self):
        self.setup_context()
        h=handoff(); h['context']['management']=contexto.logical(self.project,['app'],[])
        r=self.inspect(); h['evidence']['context_review']=contexto.review(r,'final',[])
        report=contexto.check(self.root,self.project,h,r)
        self.assertEqual(report['exit_code'],0)
        self.project['workflow']['transitions']={'mode':'enforcing','blocking_conditions':['DOCUMENTATION_IMPACT_RECONCILED'],'promotion_ref':'promotion.md'}
        self.write('promotion.md','Decision revisada')
        report=contexto.check(self.root,self.project,h,r)
        self.assertEqual(report['exit_code'],2)
        self.assertFalse(transiciones.consume(report,2,'enforcing',[],['DOCUMENTATION_IMPACT_RECONCILED'])['can_continue'])
        self.assertFalse(transiciones.consume(None,4,'informative',['REQUIRED_GATE_NOT_SATISFIED'])['can_continue'])


    def test_persisted_final_handoff_does_not_invalidate_own_git_observation(self):
        self.setup_context()
        self.write('criteria.md','Criteria'); self.write('validation.md','Validation')
        h=handoff(); h['context']['management']=contexto.logical(self.project,['app'],[])
        h['identity'].update(phase='implementacion',sender='developer')
        h['continuation']['transition']='to_test'
        observed=self.inspect()
        rows=[dict(observed['semantic']['impact'][0],operation='keep',status='unchanged_justified',justification='Contrato conservado',references=[])]
        h['evidence']['context_review']=contexto.review(observed,'final',rows)
        name='docs/hu/synthetic/handoffs/implementacion-1.json'
        self.write(name,json.dumps(h))
        result=contexto.check(self.root,self.project,h,self.inspect())
        self.assertEqual(result['findings'],[])
        # A functional path discovered afterwards must remain detectable.
        self.write('src/new.py','unreviewed')
        result=contexto.check(self.root,self.project,h,self.inspect())
        self.assertTrue(any('STALE' in x['reason'] for x in result['findings']))

    def test_final_empty_impact_and_wrong_update_target_are_not_reconciled(self):
        self.setup_context(); self.project['context_management']['impact_rules']=[]
        h=handoff(); h['context']['management']=contexto.logical(self.project,['app'],[])
        r=self.inspect(); h['evidence']['context_review']=contexto.review(r,'final',[])
        self.assertTrue(contexto.check(self.root,self.project,h,r)['findings'])
        h['evidence']['context_review']['null_reason']='Cambios internos sin impacto documental'
        self.assertEqual(contexto.check(self.root,self.project,h,r)['findings'],[])
        self.project['context_management']=policy(); h['context']['management']=contexto.logical(self.project,['app'],[])
        r=self.inspect(); row=dict(r['semantic']['impact'][0],operation='update',status='updated',justification='Actualizado',references=[{'path':'docs/shared.md'}])
        h['evidence']['context_review']=contexto.review(r,'final',[row])
        self.assertTrue(contexto.check(self.root,self.project,h,r)['findings'])

    def test_rule_documents_obey_exclusion_and_read_budget(self):
        self.setup_context()
        self.write('rules/README.md','Indice')
        self.write('rules/common.md','Estado: active\nRevisión: 1\n### COM-001\nComprobación: review\n')
        self.project['rules']={'enabled':True,'index_path':'rules/README.md','common':['rules/common.md'],'layers':{},'capabilities':{}}
        rule_context={'layers':[],'capabilities':[],'not_applicable_reason':'Documental'}
        r=self.inspect(rule_context=rule_context)
        self.assertEqual([x['id'] for x in r['semantic']['rules']],['COM-001'])
        self.project['inventory']['exclude_from_context'].append('rules/common.md')
        r=self.inspect(rule_context=rule_context)
        self.assertEqual(r['semantic']['rules'],[])
        self.assertTrue(r['semantic']['partial'])


    def test_transition_consumes_context_warnings_and_only_promoted_condition_blocks(self):
        self.setup_context(); self.write('criteria.md','Criteria'); self.write('validation.md','Validation')
        self.project['project']['setup_complete']=True
        self.write('docs/proyecto.json',json.dumps(self.project))
        h=handoff(); h['context']['management']=contexto.logical(self.project,['app'],[])
        self.write('approval.md','Apply autorizado')
        h['continuation']['authorization']={'actions':['apply'],'response_ref':{'path':'approval.md'},'context_digest':digest(git_adapter.handoff_context(h)),'candidate_digest':None,'delivery_digest':None}
        name='docs/hu/synthetic/handoffs/planificacion-1.json'; self.write(name,json.dumps(h))
        result=transiciones.check(self.root,name,'to_apply')
        self.assertEqual(result['exit_code'],0)
        self.assertTrue(any(x['condition_id']=='DOCUMENTATION_IMPACT_RECONCILED' for x in result['findings']))
        self.project['workflow']['transitions']={'mode':'enforcing','blocking_conditions':['DOCUMENTATION_IMPACT_RECONCILED'],'promotion_ref':'approval.md'}
        self.write('docs/proyecto.json',json.dumps(self.project))
        result=transiciones.check(self.root,name,'to_apply')
        self.assertEqual(result['exit_code'],2)

    def test_forged_context_metadata_cannot_hide_a_documentary_obligation(self):
        self.setup_context(); h=handoff(); h['context']['management']=contexto.logical(self.project,['app'],[])
        h['evidence']['context_review']=contexto.review(self.inspect(),'planned',[],'Sin resultados futuros')
        name='docs/hu/synthetic/handoffs/planificacion-1.json'; self.write(name,json.dumps(h))
        projection={'version':'content-v2','change':'synthetic','context':git_adapter.handoff_context(h),'history':{},'moves':[],'sync':[],'git_inputs':{}}
        self.assertTrue(git_adapter.managed(self.root,name,projection))
        h['evidence']['context_review']['git_observation']['identity']='0'*64
        self.write(name,json.dumps(h))
        with self.assertRaisesRegex(ValueError,'CONTEXT_GIT_OBSERVATION_INVALID'):
            git_adapter.managed(self.root,name,projection)


    def test_context_projection_keeps_history_and_detects_functional_document_changes(self):
        self.setup_context(); h=handoff(); h['context']['management']=contexto.logical(self.project,['app'],[])
        h['evidence']['context_review']=contexto.review(self.inspect(),'planned',[],'Mantener documentación')
        name='docs/hu/synthetic/handoffs/planificacion-1.json'; self.write(name,json.dumps(h))
        p={'version':'content-v2','change':'synthetic','context':git_adapter.handoff_context(h),'history':{name:file_hash(self.root/name)},'moves':[],'sync':[],'git_inputs':{}}
        first=git_adapter.content_view(self.root,self.base,[],p)
        self.write('docs/app.md','Edición prevista antes del plan final')
        second=git_adapter.content_view(self.root,self.base,[],p)
        self.assertNotEqual(first['input_digest'],second['input_digest'])
        self.assertTrue(git_adapter.managed(self.root,name,p))
        h['evidence']['context_review']['null_reason']='Otra justificación'
        self.write(name,json.dumps(h))
        with self.assertRaisesRegex(ValueError,'HISTORIC_HANDOFF_CHANGED'):
            git_adapter.content_view(self.root,self.base,[],p)

    def test_functional_context_sync_target_requires_plan_reconciliation(self):
        self.setup_context(); h=handoff(); h['context']['management']=contexto.logical(self.project,['app'],[])
        target='docs/app.md'
        p={'version':'content-v2','change':'synthetic','context':git_adapter.handoff_context(h),'history':{},'moves':[],'sync':[{'path':target,'before_sha256':file_hash(self.root/target),'after_sha256':file_hash(self.root/target),'before_entry':None}],'git_inputs':{}}
        with self.assertRaisesRegex(ValueError,'SYNC_TARGET_IS_A_CONTEXT_INPUT_RECONCILE_PLAN'):
            git_adapter.content_view(self.root,self.base,[],p)

    def test_synthetic_silver_context_does_not_activate_remote_runtime(self):
        self.setup_context()
        self.project['context_management']['components'][0]['paths'].append('notebooks/silver/*')
        self.write('notebooks/silver/new.py','# synthetic Spark fixture')
        r=self.inspect(components=['app'],triggers=['tests'])
        self.assertIn('app',r['semantic']['components'])
        self.assertEqual(r['metrics']['remote_processes'],0)
        # The executable catalog remains the existing authority, with required Spark inactive.
        from testing.common import contract
        cfg=read(KIT/'docs/pruebas/capabilities.json')
        self.assertTrue(any(not row['enabled'] for row in cfg['adapters'].values()))


    def test_impact_only_target_is_frozen_and_sync_remains_functional(self):
        self.setup_context(); self.project['context_management']['components'][0]['documents']=[]
        cm=contexto.logical(self.project,['app'],[])
        self.assertIn('docs/app.md',[x['path'] for x in cm['documents']])

    def test_final_review_survives_role_specific_sources(self):
        self.setup_context()
        self.project['context_management']['components'][1]['documents'][0]['roles']=['developer']
        h=handoff(); h['context']['management']=contexto.logical(self.project,['app'],[])
        r=self.inspect(); rows=[dict(r['semantic']['impact'][0],operation='keep',status='unchanged_justified',justification='Se conserva',references=[])]
        h['evidence']['context_review']=contexto.review(r,'final',rows)
        fresh=contexto.inspect(self.root,self.project,'synthetic','reviewer','revision',self.base)
        self.assertEqual(contexto.check(self.root,self.project,h,fresh)['findings'],[])

    def test_document_deletion_is_complete_when_git_and_final_disposition_agree(self):
        self.setup_context(); self.git('add','--','docs/app.md'); self.git('commit','-m','baseline document')
        self.base=self.git('rev-parse','HEAD'); self.git('rm','docs/app.md')
        h=handoff(); h['context']['management']=contexto.logical(self.project,['app'],[])
        preliminary=self.inspect(); row=dict(preliminary['semantic']['impact'][0],operation='delete',status='updated',justification='Documento retirado por contrato eliminado',references=[])
        r=self.inspect(dispositions=[row]); self.assertFalse(r['semantic']['partial'])
        h['evidence']['context_review']=contexto.review(r,'final',[row])
        self.assertEqual(contexto.check(self.root,self.project,h,r)['findings'],[])
        contexto.validate_metadata(self.root,self.project,h)


    def test_duplicate_rule_ids_are_rejected_independently_of_order(self):
        self.setup_context(); other=copy.deepcopy(self.project['context_management']['impact_rules'][0]); other['reason']='Otro significado'
        self.project['context_management']['impact_rules'].append(other)
        for rules in [self.project['context_management']['impact_rules'],list(reversed(self.project['context_management']['impact_rules']))]:
            self.project['context_management']['impact_rules']=rules
            with self.assertRaisesRegex(ValueError,'CONTEXT_DUPLICATE_IMPACT_RULE'):
                self.inspect()

    def test_unknown_path_contains_responsible_action_without_invented_mapping(self):
        self.setup_context(); self.write('new/component.py','new component')
        result=self.inspect()
        pending=[x for x in result['semantic']['pending'] if x['path']=='new/component.py']
        self.assertEqual(pending[0]['owner'],'planner')
        self.assertEqual(pending[0]['action'],'review_component_mapping')
        self.assertNotIn('new',result['semantic']['components'])


    def test_context_adopted_plan_run_gate_resumes_after_reference_correction(self):
        base,policy_path,execution_path,outputs=legacy.AdaptersTests.local_setup(self)
        project=read(KIT/'docs/proyecto.json'); project['project']['setup_complete']=True
        project['context_management']=policy()
        project['context_management']['components'][0]['dependencies']=[]
        project['context_management']['components']=project['context_management']['components'][:1]
        self.write('docs/app.md','Documentación funcional vigente')
        self.write('criteria.md','CA01/CA02'); self.write('validation.md','Plan preliminar')
        project['validation']['testing'].update(policy_path='policy.json',execution_path='execution.json')
        self.write('docs/proyecto.json',json.dumps(project))
        p=read(policy_path); p['rules'].append({'id':'DOCS','paths':['docs/*','criteria.md','validation.md'],'checks':[],'reason':'Documentación sintética revisada'})
        self.write('policy.json',json.dumps(p))
        execution=read(execution_path); execution['reviewed_policy_digest']=digest(p); self.write('execution.json',json.dumps(execution))
        h=handoff(); h['context']['management']=contexto.logical(project,['app'],[])
        h['scope']['git_inputs']={'unit':[]}
        observation=contexto.inspect(self.root,project,'synthetic','planner','planificacion',base)
        h['evidence']['context_review']=contexto.review(observation,'planned',[],'Plan documental revisado')
        self.write('docs/hu/synthetic/handoffs/planificacion-1.json',json.dumps(h))
        plan=workflow.make_plan(self.root,policy_path,execution_path,base,['CA01','CA02'])
        self.assertEqual(plan['status'],'ready')
        result=workflow.run(self.root,policy_path,execution_path,plan)
        self.assertEqual(result['records'][0]['status'],'passed')
        h['identity'].update(phase='implementacion',sender='developer')
        h['continuation']['transition']='to_test'
        observed=contexto.inspect(self.root,project,'synthetic','developer','implementacion',base)
        row=dict(observed['semantic']['impact'][0],operation='keep',status='unchanged_justified',justification='La descripción mantiene el contrato',references=[{'path':'docs/app.md','sha256':file_hash(self.root/'docs/app.md')}])
        h['evidence']['context_review']=contexto.review(observed,'final',[row])
        name='docs/hu/synthetic/handoffs/implementacion-1.json'; self.write(name,json.dumps(h))
        with patch.object(workflow.execution,'run_process',side_effect=AssertionError('gate relanzó suites')):
            self.assertEqual(workflow.gate(self.root,policy_path,execution_path,plan,result)['status'],'passed')
            h['identity']['attempt']=2; h['previous_handoff']={'path':name,'sha256':file_hash(self.root/name)}
            h['evidence']['artifacts']=[{'path':'docs/app.md','sha256':file_hash(self.root/'docs/app.md')}]
            self.write(name.replace('-1.json','-2.json'),json.dumps(h))
            self.assertEqual(workflow.gate(self.root,policy_path,execution_path,plan,result)['status'],'passed')
            self.write('docs/app.md','Cambio funcional después de Tester')
            self.assertEqual(workflow.gate(self.root,policy_path,execution_path,plan,result)['status'],'blocked')


    def test_real_junction_is_rejected_before_document_read(self):
        import subprocess
        self.setup_context(); real=self.root/'real'; real.mkdir(); (real/'doc.md').write_text('NO CARGAR',encoding='utf-8')
        link=self.root/'linked'
        created=subprocess.run(['cmd','/c','mklink','/J',str(link),str(real)],capture_output=True,text=True)
        self.assertEqual(created.returncode,0,created.stderr)
        self.addCleanup(link.rmdir)
        self.project['context_management']['components'][0]['documents'].append(document('linked/doc.md'))
        result=self.inspect()
        self.assertIn({'path':'linked/doc.md','reason':'unsafe_path'},result['semantic']['omitted'])
        self.assertNotIn('linked/doc.md',[x['path'] for x in result['semantic']['sources']])

    def test_silver_required_inactive_runtime_stays_blocked_without_process(self):
        self.setup_context()
        from testing.common import contract
        p=read(KIT/'.agents/skills/Crea/crea-pruebas/assets/policy.template.json')
        p['setup_complete']=True
        p['checks']=[{'id':'spark','kind':'runtime','environment':'databricks','effect':'remote_read','argv':[],
            'configured':False,'timeout_seconds':60,'inputs':['notebooks/silver/*'],'criteria':['CA-SPARK'],
            'min_tests':1,'required_assertions':['CA-SPARK'],'reuse_seconds':0}]
        p['rules']=[{'id':'SILVER','paths':['notebooks/silver/*'],'checks':['spark'],'reason':'Runtime requerido por comportamiento'}]
        self.write('notebooks/silver/job.py','# Spark sintético')
        observation=self.inspect(components=['app'],triggers=['tests'])
        plan=contract.build_plan(self.root,p,[{'path':'notebooks/silver/job.py','old_path':None,'status':'A'}],self.base,['CA-SPARK'])
        self.assertEqual(plan['status'],'blocked')
        self.assertIn('CHECK_NOT_CONFIGURED',str(plan['blockers']))
        self.assertEqual(observation['metrics']['suite_processes'],0)
        self.assertEqual(observation['metrics']['remote_processes'],0)


    def test_inspection_process_guard_allows_only_local_git(self):
        import subprocess
        self.setup_context(); calls=[]; original=subprocess.run
        def local_git_only(argv,*args,**kwargs):
            self.assertEqual(argv[0],'git')
            self.assertFalse(set(argv)&{'push','pull','fetch','clone','ls-remote'})
            calls.append(argv)
            return original(argv,*args,**kwargs)
        with patch.object(subprocess,'run',local_git_only):
            result=self.inspect()
        self.assertEqual(len(calls),result['metrics']['git_processes'])
        self.assertEqual(result['metrics']['suite_processes'],0)
        self.assertEqual(result['metrics']['remote_processes'],0)


    def test_final_source_observations_cannot_be_silently_removed(self):
        self.setup_context(); h=handoff(); h['context']['management']=contexto.logical(self.project,['app'],[])
        r=self.inspect(); rows=[dict(r['semantic']['impact'][0],operation='keep',status='unchanged_justified',justification='Se conserva',references=[])]
        h['evidence']['context_review']=contexto.review(r,'final',rows)
        h['evidence']['context_review']['sources']=[]
        self.assertTrue(any('SOURCE' in x['reason'] for x in contexto.check(self.root,self.project,h,r)['findings']))

    def test_updated_document_cannot_redirect_to_an_unrelated_target(self):
        self.setup_context(); h=handoff(); h['context']['management']=contexto.logical(self.project,['app'],[])
        r=self.inspect(); row=dict(r['semantic']['impact'][0],operation='update',status='updated',target_path='docs/shared.md',justification='Cambio',references=[{'path':'docs/shared.md','sha256':file_hash(self.root/'docs/shared.md')}])
        h['evidence']['context_review']=contexto.review(r,'final',[row])
        self.assertTrue(contexto.check(self.root,self.project,h,r)['findings'])
        with self.assertRaises(ValueError): schemas.validate_schema(read(KIT/'docs/plantillas/handoff.schema.json'),h)

    def test_moved_target_is_checked_for_exclusion_history_and_limits_before_read(self):
        self.setup_context(); original='docs/app.md'; self.git('add','--',original); self.git('commit','-m','doc baseline')
        self.base=self.git('rev-parse','HEAD')
        targets=['.env','openspec/changes/archive/old/doc.md','docs/oversized.md']
        for target in targets:
            if (self.root/target).exists(): (self.root/target).unlink()
            if not (self.root/original).exists(): self.write(original,'approved')
            (self.root/target).parent.mkdir(parents=True,exist_ok=True)
            (self.root/original).rename(self.root/target)
            if target.endswith('oversized.md'): self.project['context_management']['limits']['per_document_bytes']=2
            row={'path':original,'rule':'paths','reason':'Conservar referencias del componente','owner':'developer','operation':'move','status':'updated','target_path':target,'justification':'Movimiento previsto','references':[{'path':target,'sha256':file_hash(self.root/target)}]}
            calls=[]; original_open=Path.open
            def watch(path,*args,**kw):
                calls.append(path.relative_to(self.root).as_posix()); return original_open(path,*args,**kw)
            with patch.object(Path,'open',watch):
                r=self.inspect(dispositions=[row],moves=[{'from':original,'to':target,'sha256':row['references'][0]['sha256']}])
            reason='excluded' if target=='.env' else 'history_not_explicit' if '/archive/' in target else 'byte_limit'
            self.assertIn({'path':original,'reason':reason},r['semantic']['omitted'])
            self.assertNotIn(target,calls)
            self.assertTrue(r['semantic']['partial'])
            (self.root/target).rename(self.root/original)

if __name__=='__main__': unittest.main()









