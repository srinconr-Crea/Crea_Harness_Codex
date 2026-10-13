"""Impact selection and offline checks. Never imports client Python code."""
import ast
import json
import os
from pathlib import Path
import re
import sys

import yaml

from harness_core.validation import ValidationPlan, ValidationTest, validate_request, make_evidence
from harness_core.onboarding_plan import canonical, sha
from harness_core.configuration import safe_path
from .quality_resources import load_quality


def select_plan(*,client_id,run_id,attempt,candidate_sha256,plan_revision,technologies,impacts,
    performance_baseline_sha256=None):
    quality=load_quality(); tests=[]
    def add(test_id,technology,layer,scope,required=True):
        rules=[r.id for r in quality.practices.rules if r.technology in (technology,'general')]
        tests.append(ValidationTest(schema_version=1,test_id=test_id,technology=technology,layer=layer,
            required=required,scope=scope,rule_ids=rules))
    for tech in technologies:
        add(tech+'-static',tech,'L0','offline-syntax')
        if tech=='python': add('python-unit',tech,'L1','isolated-behavior')
        if tech=='pyspark': add('spark-unit',tech,'L1','isolated-spark')
        if tech=='sql': add('sql-semantic',tech,'L2','runtime-semantics')
        if tech=='notebook': add('notebook-integration',tech,'L3','fresh-job')
        if tech=='yaml-dabs' and 'integration' in impacts: add('bundle-validate',tech,'L3','authorized-bundle')
    if 'delta' in impacts: add('delta-semantic','sql','L2','delta-runtime')
    elif 'runtime' in impacts and not any(t.layer=='L2' for t in tests): add('runtime-semantic','pyspark','L2','runtime-semantics')
    if 'integration' in impacts and not any(t.layer=='L3' for t in tests): add('job-integration','notebook','L3','fresh-job')
    if 'performance' in impacts: add('performance','general','L2','reproducible-baseline',performance_baseline_sha256 is not None)
    ids=[c.id for c in quality.tests.cases if c.implementation_change=='05-databricks-validation-and-evidence'
        and c.technology in technologies]
    value=dict(schema_version=1,client_id=client_id,run_id=run_id,attempt=attempt,candidate_sha256=candidate_sha256,
        plan_revision=plan_revision,practice_pack_sha256=sha(canonical(quality.practices.model_dump())),
        technologies=technologies,impacts=impacts,tests=[t.model_dump() for t in tests],catalog_test_ids=ids,
        performance_baseline_sha256=performance_baseline_sha256)
    return ValidationPlan(**value,plan_sha256=sha(canonical(value)))


def static_check(plan,request,raw,*,filename,root=None):
    test=validate_request(plan,request)
    if test.layer!='L0': raise ValueError('static_scope_mismatch')
    if request.tool_sha256!=sha(Path(__file__).read_bytes()) or request.runtime_sha256!=sha(sys.version.encode()) or request.command!=['harness','validate','static']:
        return make_evidence(request,'blocked',scope='offline-syntax',reason='static_tool_mismatch')
    if request.source_sha256 is not None and sha(raw)!=request.source_sha256:
        return make_evidence(request,'blocked',scope='offline-syntax',reason='source_hash_mismatch')
    if len(raw)>1024*1024: return make_evidence(request,'blocked',scope='offline-syntax',reason='input_too_large')
    try:
        text=raw.decode('utf-8-sig')
        if test.technology in ('python','pyspark'):
            tree=ast.parse(text,filename=filename)
            if test.technology=='pyspark' and any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
                and n.func.attr in ('collect','toPandas') for n in ast.walk(tree)):
                raise ValueError('unbounded_driver_materialization')
        elif test.technology in ('yaml-dabs','cicd'):
            data=yaml.safe_load(text)
            if not isinstance(data,dict): raise ValueError('yaml_mapping_required')
            if test.technology=='cicd':
                for name,job in data.get('jobs',{}).items():
                    if any(word in name.lower() for word in ('deploy','publish','promote')):
                        if not job.get('needs') or 'always(' in str(job.get('if','')).replace(' ',''):
                            raise ValueError('promotion_without_success_gate')
            if test.technology=='yaml-dabs' and root is not None:
                root=safe_path(root); base=root/filename
                def paths(value):
                    if isinstance(value,dict):
                        for key,item in value.items():
                            if key in ('python_file','notebook_path') and isinstance(item,str):
                                path=Path(os.path.normpath(base.parent/item))
                                if path.resolve().is_relative_to(root.resolve()) and safe_path(path).is_file(): continue
                                raise ValueError('relative_resource_missing')
                            paths(item)
                    elif isinstance(value,list):
                        for item in value: paths(item)
                paths(data)
        elif test.technology=='notebook':
            data=json.loads(text)
            if data.get('nbformat')!=4 or not isinstance(data.get('cells'),list): raise ValueError('notebook_format')
            for cell in data['cells']:
                if cell.get('cell_type')=='code': ast.parse(''.join(cell['source']))
        elif test.technology=='sql':
            try: import sqlglot
            except ImportError: return make_evidence(request,'blocked',scope='offline-syntax',reason='sql_parser_absent')
            try: sqlglot.parse(text,read='databricks')
            except sqlglot.errors.SqlglotError:
                return make_evidence(request,'failed',scope='offline-syntax',reason='sql_parse_failed')
        else: return make_evidence(request,'blocked',scope='offline-syntax',reason='static_unsupported')
    except (SyntaxError,ValueError,UnicodeError,yaml.YAMLError,KeyError,TypeError):
        return make_evidence(request,'failed',scope='offline-syntax',reason='static_check_failed')
    return make_evidence(request,'passed',scope='offline-syntax',result={'source_sha256':sha(raw),'syntax_only':True,
        'python_version':sys.version,'tool_sha256':sha(Path(__file__).read_bytes())},observed=True)
