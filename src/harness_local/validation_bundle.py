"""Restricted bundle validate is authenticated and distinct from offline YAML."""
import json
from pathlib import Path
import shutil
import subprocess
import uuid

import yaml

from harness_core.configuration import safe_path,ConfigError
from harness_core.validation import validate_request,make_evidence
from harness_core.onboarding_plan import sha
from .validation_remote import DatabricksCLI


def run_bundle(plan,request,target,raw,*,state_dir,provider=None):
    test=validate_request(plan,request); provider=provider or DatabricksCLI()
    if test.test_id!='bundle-validate': raise ValueError('bundle_scope_mismatch')
    def blocked(reason): return make_evidence(request,'blocked',scope=test.scope,reason=reason,simulated=provider.simulated)
    if target is None: return blocked('sandbox_not_selected')
    if not target.authorized or not target.synthetic or 'bundle' not in target.modes: return blocked('sandbox_unauthorized')
    try:
        config=yaml.safe_load(raw.decode('utf-8'))
        if not isinstance(config,dict) or set(config)-{'bundle','workspace','resources'}: return blocked('bundle_config_unsupported')
        if set(config.get('bundle',{}))-{'name'} or not config.get('bundle',{}).get('name'): return blocked('bundle_config_unsupported')
        if config.get('workspace')!={'host':target.host}: return blocked('bundle_target_mismatch')
        resources=config.get('resources',{})
        if set(resources)-{'jobs'}: return blocked('bundle_resources_unsupported')
        for job in resources.get('jobs',{}).values():
            if set(job)-{'name','tasks'}: return blocked('bundle_resources_unsupported')
            tasks=job.get('tasks',[])
            if len(tasks)!=1 or set(tasks[0])!={'task_key','notebook_task'}: return blocked('bundle_resources_unsupported')
            if tasks[0]['notebook_task']!={'notebook_path':target.resources[0]}: return blocked('bundle_target_mismatch')
    except (UnicodeError,ValueError,TypeError,AttributeError,yaml.YAMLError): return blocked('bundle_config_invalid')
    if request.source_sha256!=sha(raw): return blocked('source_hash_mismatch')
    try:
        observed=provider.preflight(target)
        fields=('profile','host','caller_identity','execution_identity','job_id','runtime','volume','resources','job_settings_sha256','notebook_sha256','synthetic')
        if any(observed.get(f)!=getattr(target,f) for f in fields): return blocked('sandbox_identity_mismatch')
    except (OSError,ValueError,KeyError,subprocess.SubprocessError,ConfigError): return blocked('sandbox_preflight_unavailable')
    state=safe_path(state_dir); state.mkdir(parents=True,exist_ok=True)
    stage=state/('bundle-'+uuid.uuid4().hex); stage.mkdir()
    try:
        (stage/'databricks.yml').write_bytes(raw)
        resolved=provider.bundle_validate(target,stage)
        if resolved.get('workspace',{}).get('host')!=target.host: return blocked('bundle_target_mismatch')
        return make_evidence(request,'passed',scope=test.scope,result={'source_sha256':sha(raw),'bundle_validated':True,
            'notebook_executed':False,'deploy_executed':False},observed=True,simulated=provider.simulated)
    except (OSError,ValueError,KeyError,subprocess.SubprocessError,ConfigError): return blocked('bundle_validation_unavailable')
    finally:
        # Only this generated stage, never the client tree or arbitrary resolved path.
        checked=safe_path(stage)
        if checked.parent!=state or not checked.name.startswith('bundle-'): raise ValueError('bundle_cleanup_rejected')
        shutil.rmtree(checked)
