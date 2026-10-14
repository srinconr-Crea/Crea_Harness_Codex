"""Compose installation/onboarding with a single immutable parent approval.

Legacy adapters retain their contracts, hashes and recovery journals. This
facade never treats a local preparation as Desktop or remote certification.
"""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import uuid
from functools import wraps

from pydantic import Field, ValidationError

from harness_core.configuration import ConfigError, digest, load_document, safe_path, normalize_remote
from harness_core.contracts import Descriptor,Policy,Binding
from harness_core.guided import SafeContract, QuestionnaireDraft, GuidedOnboardingPlan, sanitize
from harness_core.onboarding_plan import canonical,sha,load_json,absolute_path,separate
from harness_core.setup import SetupInput,SetupPlan,SetupReport,InstallationRecord,SetupEffect,InstalledTool
from . import guided_onboarding as guided
from .desktop_resources import render_integration,resource_digest
from .diagnostics import probe,git_read,local_status
from .execution_state import CheckoutLock,ensure_state,persist
from .windows_fs import PinnedTree
from .tool_runtime import installation_tools, executable,discover,using_tools


def checkpoint(stage):
    """Fault-injection seam; no production side effect."""


def installed_operation(function):
    @wraps(function)
    def call(first,*args,**kwargs):
        if isinstance(first,dict): selected=first.get('installation_record')
        else: selected=load_json(first,SetupPlan).inputs.installation_record
        installation=load_json(selected,InstallationRecord,limit=8*1024*1024) if selected else None
        if function.__name__=='preview':
            needed={'git'}
            if 'openspec' in first.get('capabilities',[]): needed.update(('node','openspec'))
            if 'databricks' in first.get('capabilities',[]): needed.add('databricks')
            tools=discover(installation,needed)
        else:
            plan=load_json(first,SetupPlan)
            recipe=json.loads(plan.child_payloads['tools']) if 'tools' in plan.child_payloads else None
            from harness_core.setup import InstalledTool
            tools=[InstalledTool.model_validate(t) for t in recipe['existing']] if recipe else discover(installation)
            if recipe and installation:
                names={t.name for t in tools}|{op['name'] for op in recipe['operations']}
                selected={t.name:t for t in tools}
                selected.update({t.name:t for t in installation.tools if t.name in names})
                tools=list(selected.values())
        with using_tools(tools): return function(first,*args,**kwargs)
    return call


def digest(path):
    # A composite parent embeds its children and can exceed the v1 input limit.
    path=safe_path(path)
    with PinnedTree(path.parent) as tree:
        with tree.file(path.name) as handle: return sha(handle.read(8*1024*1024))


class SetupJournal(SafeContract):
    plan_sha256: str
    parent_sha256: str
    target_identity: str
    child_path: str
    stages: list[dict] = Field(max_length=8)
    state: str
    owned: dict[str,str]
    observations: dict[str,dict] = Field(default_factory=dict)
    updated_installation_sha256: str | None = None


def interview(raw):
    sanitize(raw)
    fields=set(SetupInput.model_fields)
    if not isinstance(raw,dict) or set(raw)-fields: raise ConfigError('invalid_input')
    values=dict(raw); sources=dict(values.get('sources',{}))
    from harness_core.setup import AccessScope
    for name,model in (('descriptor',Descriptor),('policy',Policy),('binding',Binding),('access_scope',AccessScope)):
        if isinstance(values.get(name),str):
            values[name]=load_document(values[name],model).model_dump(); sources[name]='file'
    for name in ('descriptor','policy','binding','access_scope','capabilities'):
        if name in values: sources.setdefault(name,'user')
    values['sources']=sources
    if isinstance(values.get('guided_request'),dict) and isinstance(values.get('descriptor'),dict):
        for key in ('repository','base_branch'):
            values['guided_request'].setdefault(key,values['descriptor'].get(key))
    required=('descriptor','policy','binding','access_scope','capabilities','guided_request')
    questions=[dict(field=n,reason='missing_decision') for n in required if values.get(n) is None]
    if not questions:
        try: values=SetupInput.model_validate(values).model_dump()
        except (ValueError,ValidationError,ConfigError): raise ConfigError('identity_mismatch') from None
    return dict(schema_version=1,command='setup',status='blocked' if questions else 'ready',checks=[],questions=questions,values=values)


def request_draft(request):
    return QuestionnaireDraft(schema_version=1,answers={k:dict(value=v,status='known',source='user',confirmed=True)
        for k,v in request.model_dump(exclude={'kind','schema_version'}).items() if v is not None})


def result(**data):
    return dict(schema_version=1,command='setup',checks=[],**data)


def record(plan):
    if not plan.inputs.installation_record: return None
    return load_json(plan.inputs.installation_record,InstallationRecord,limit=8*1024*1024)


def selected_tools(plan):
    recipe=json.loads(plan.child_payloads['tools'])
    tools={t['name']:InstalledTool.model_validate(t) for t in recipe['existing']}
    names=set(tools)|{op['name'] for op in recipe['operations']}
    installation=record(plan)
    if installation: tools.update({t.name:t for t in installation.tools if t.name in names})
    return list(tools.values())


@installed_operation
def preview(raw, *, probe_fn=probe,plan_out=None):
    imported=interview(raw)
    if imported['questions']: return imported,2
    inputs=SetupInput.model_validate(imported['values']); r=inputs.guided_request
    if r is None: raise ConfigError('invalid_input')
    if digest(r.policy_path)!=inputs.binding.policy_sha256 or load_document(r.policy_path,Policy)!=inputs.policy:
        raise ConfigError('identity_mismatch')
    if load_document(r.binding_path,Binding)!=inputs.binding: raise ConfigError('identity_mismatch')
    target=absolute_path(inputs.binding.target_path)
    blockers=[]; effects=[]; child_payloads={}; technical=['.harness/client.yaml']; writes=[]
    run_id=uuid.uuid4().hex
    hashes={'policy':digest(r.policy_path),'binding':digest(r.binding_path),'desktop_kit':resource_digest()}
    if inputs.installation_record:
        installation=load_json(inputs.installation_record,InstallationRecord,limit=8*1024*1024)
        hashes['installation']=digest(inputs.installation_record)
        if not installation.resource_installed: blockers.append('tool_unavailable')
    else: installation=None
    from .setup_tools import plan_tools
    needed={'git'}|({'node','openspec'} if 'openspec' in inputs.capabilities else set())|({'databricks'} if 'databricks' in inputs.capabilities else set())
    tool_plan=plan_tools(inputs,discover(installation,needed))
    child_payloads['tools']=canonical(tool_plan).decode()
    if tool_plan['blocked']: blockers.append('tool_unavailable')
    effects.extend(dict(schema_version=1,kind='install',destination=op['destination'],description='Herramienta oficial fijada '+op['name'],artifact_sha256=op['sha256']) for op in tool_plan['operations'])
    if tool_plan['operations']:
        effects.append(dict(schema_version=1,kind='integrate',destination=inputs.installation_record,description='Actualizar ownership de herramientas en registro de producto'))
    has_git=any(t['name']=='git' for t in tool_plan['existing'])
    if target.exists() and has_git:
        if inputs.clone: raise ConfigError('owned_resource_conflict')
        if load_document(target/'.harness/client.yaml',Descriptor)!=inputs.descriptor: raise ConfigError('identity_mismatch')
        origin=git_read(target,'remote','get-url','origin')
        if normalize_remote(origin)!=inputs.descriptor.repository.lower(): raise ConfigError('identity_mismatch')
        if inputs.commit_local:
            # No previously staged user change can enter the reviewed commit.
            indexed=git_read(target,'diff','--cached','--name-only','--no-ext-diff')
            if indexed: blockers.append('owned_resource_conflict')
        # Preview may inspect an uncommitted fresh descriptor; reject an existing
        # application checkout with unrelated tracked/untracked user changes.
        with PinnedTree(target) as tree: hashes['target_identity']=sha(tree.base.identity().encode())
        child,code=guided.preview(request_draft(r),probe_fn=probe_fn)
        parsed=GuidedOnboardingPlan.model_validate(child['plan'])
        child_payloads['onboarding']=canonical(parsed.model_dump()).decode()
        if code: blockers.append('owned_resource_conflict')
        writes=sorted(set(o.path for o in parsed.preparation.operations if o.scope=='target') | {e.path for e in parsed.integration_edits})
        # Changed customer files require a separate checkout decision. Managed
        # configuration is reviewed in the child, including custom instructions.
        changed=set(git_read(target,'ls-files','--modified','--others','--exclude-standard').splitlines())
        changed.update(git_read(target,'diff','--cached','--name-only','--no-ext-diff').splitlines())
        changed.update(git_read(target,'ls-files','--others','--exclude-standard').splitlines())
        managed=set(writes)|{'.harness/client.yaml','.harness/access-scope.json','AGENTS.md','.codex/config.toml'}
        managed.update(p.relative_to(target).as_posix() for p in (target/'.codex/agents').glob('*.toml'))
        if changed-managed: blockers.append('owned_resource_conflict')
        technical=sorted(set(technical+list(parsed.preparation.input_hashes)+writes))
        technical=[('.harness/client.yaml' if p=='descriptor' else p) for p in technical if p not in ('policy','binding','tools')]
        gitroot=safe_path(target/'.git')
        if not gitroot.is_dir(): raise ConfigError('owned_resource_conflict')
        for path in gitroot.rglob('*'):
            path=safe_path(path)
            if path.is_file(): technical.append(path.relative_to(target).as_posix())
        # Standalone agents use the supported host schema. Ignored legacy
        # settings remain user-owned; adaptation requires a reviewed new plan.
        import tomllib
        agentdir=safe_path(target/'.codex/agents')
        if agentdir.exists():
            for agentfile in agentdir.glob('*.toml'):
                config=tomllib.loads(safe_path(agentfile).read_text(encoding='utf-8'))
                if not {'name','description','developer_instructions'}<=set(config) or {'sandbox_mode','approval_policy'}&set(config):
                    blockers.append('permission_conflict')
        effects.extend(dict(schema_version=1,kind='integrate',destination=str(target/p),description='Recurso gestionado exacto de plan hijo') for p in writes)
        effects.extend(dict(schema_version=1,kind='create',destination=o.path,description='Configuración externa exacta del plan hijo') for o in parsed.preparation.operations if o.scope!='target')
        effects.append(dict(schema_version=1,kind='create',destination=guided.tool_path(parsed.preparation),description='Vinculación de herramientas del plan hijo'))
    else:
        if not target.exists() and not inputs.clone: blockers.append('invalid_input')
        # The frozen recipe may only create absent managed paths after cloning.
        # Unknown conflicting remote resources require a new parent review.
        from .setup_recipe import recipe
        frozen=recipe(inputs)
        child_payloads['managed_recipe']=canonical(frozen).decode()
        payload=canonical(r.model_dump()).decode(); child_payloads['checkout_recipe']=payload
        writes=sorted(set(frozen['prepare'])|set(frozen['integrate']))
        effects.extend(dict(schema_version=1,kind='create',destination=str(target/p),description='Crear únicamente si ausente; contenido fijado en receta') for p in writes)
        effects.extend(dict(schema_version=1,kind='create',destination=p,description='Configuración externa fijada en receta') for p in frozen['external'])
        if inputs.clone: effects.append(dict(schema_version=1,kind='clone',destination=str(target),description='Clonar URL/base seleccionadas, sin push'))
    if inputs.remote_read:
        effects.extend([dict(schema_version=1,kind='auth',destination=inputs.databricks_host,description='OAuth nativo con perfil seleccionado'),
            dict(schema_version=1,kind='read',destination=inputs.databricks_host,description='Lectura current-user me, sin jobs/deploy/escrituras')])
    if inputs.commit_local:
        effects.append(dict(schema_version=1,kind='local_commit',destination=str(target),description='Commit local solo de recursos gestionados revisados; sin push'))
    from harness_core.onboarding_plan import Operation,authorize
    scope_content=(canonical(inputs.access_scope.model_dump())+b'\n').decode()
    scope_file=target/'.harness/access-scope.json'
    own_operations=[]
    if safe_path(scope_file).exists():
        if digest(scope_file)!=sha(scope_content.encode()): blockers.append('owned_resource_conflict')
        hashes['scope_file']=digest(scope_file)
    else:
        own_operations=[Operation(schema_version=1,scope='target',path='.harness/access-scope.json',content=scope_content,sha256=sha(scope_content.encode()))]
        if authorize(own_operations,inputs.policy): blockers.append('access_denied')
        writes=sorted(set(writes)|{'.harness/access-scope.json'})
        effects.append(dict(schema_version=1,kind='create',destination=str(scope_file),description='Alcance portable versionado, contenido fijado'))
    technical=sorted(set(technical)|{'.harness/access-scope.json'})
    effects.extend([
        dict(schema_version=1,kind='create',destination=inputs.binding.state_dir,description='Estado del checkout: locks y journals propios, sin SQLite durante preview'),
        dict(schema_version=1,kind='create',destination=str(Path(inputs.binding.state_dir)/('setup-'+run_id)),description='Journal padre y recibos de observaciones inmutables'),
        dict(schema_version=1,kind='create',destination=str(Path(r.binding_path).with_name('setup-'+run_id+'-child.json')),description='Plan hijo materializado y verificado contra el padre'),
        dict(schema_version=1,kind='create',destination=str(Path(r.binding_path).with_name(Path(r.binding_path).name+'.setup.json')),description='Vinculación local del alcance y herramientas revisados')])
    names=['validate','tools','checkout','prepare','integrate','auth','check','report']
    child_plans={k:sha(v.encode()) for k,v in child_payloads.items()}
    effects=[SetupEffect.model_validate(e).model_dump() for e in effects]
    value=dict(schema_version=1,kind='setup_plan',run_id=run_id,inputs=inputs.model_dump(),input_hashes=hashes,
        child_plans=child_plans,child_payloads=child_payloads,setup_operations=[o.model_dump() for o in own_operations],stages=[dict(schema_version=1,name=n,dependencies=names[:i],
            child_sha256=child_plans.get('onboarding') if n=='prepare' else None,status='pending',reason=None) for i,n in enumerate(names)],
        technical_reads=sorted(set(technical)),integration_writes=writes,effects=effects,applicable=not blockers,blockers=blockers)
    plan=SetupPlan.model_validate({**value,'plan_sha256':sha(canonical(value))})
    if plan_out:
        guided.export(plan_out,plan.model_dump(),[r.target_path,r.policy_path,r.binding_path,inputs.binding.state_dir])
    return result(status='prepared' if plan.applicable else 'blocked',plan=plan.model_dump(),certified=False,release_allowed=False), (0 if plan.applicable else 4)


def folder(plan): return safe_path(Path(plan.inputs.binding.state_dir)/('setup-'+plan.run_id))


def select(path,authorization=None):
    plan=load_json(path,SetupPlan)
    if authorization is not None and authorization!=plan.plan_sha256: raise ConfigError('plan_stale')
    if not plan.applicable or not plan.inputs.guided_request: raise ConfigError('invalid_input')
    r=plan.inputs.guided_request
    separate([str(path),r.target_path,r.policy_path,r.binding_path,plan.inputs.binding.state_dir])
    if digest(r.policy_path)!=plan.input_hashes['policy'] or digest(r.binding_path)!=plan.input_hashes['binding']:
        raise ConfigError('plan_stale')
    if resource_digest()!=plan.input_hashes['desktop_kit']: raise ConfigError('plan_stale')
    target=absolute_path(plan.inputs.binding.target_path)
    if 'target_identity' in plan.input_hashes:
        with PinnedTree(target) as tree:
            if sha(tree.base.identity().encode())!=plan.input_hashes['target_identity']: raise ConfigError('plan_stale')
    if 'scope_file' in plan.input_hashes and digest(target/'.harness/access-scope.json')!=plan.input_hashes['scope_file']:
        raise ConfigError('plan_stale')
    if plan.inputs.installation_record:
        expected=plan.input_hashes.get('installation')
        if (folder(plan)/'journal.json').exists():
            own=load_json(folder(plan)/'journal.json',SetupJournal)
            expected=own.updated_installation_sha256 or expected
        if digest(plan.inputs.installation_record)!=expected: raise ConfigError('plan_stale')
    return plan


def journal(plan):
    value=load_json(folder(plan)/'journal.json',SetupJournal)
    if value.plan_sha256!=plan.plan_sha256: raise ConfigError('owned_resource_conflict')
    for path,expected in value.owned.items():
        if digest(path)!=expected: raise ConfigError('owned_resource_conflict')
    return value


def capability_report(plan,run):
    stages={s['name']:s['status'] for s in run.stages}
    prepared=stages.get('prepare')=='completed'
    caps=[]
    for name in ('local','desktop','git','openspec','databricks'):
        reason='remote_not_checked' if name=='databricks' else 'skill_discovery_pending' if name=='desktop' else 'tool_unavailable'
        observation=run.observations.get(name)
        if observation and all(datetime.fromisoformat(e['valid_until'])>datetime.now(timezone.utc) for e in observation['evidence']):
            caps.append(observation)
        else:
            failure=next((s['reason'] for s in run.stages if s['name'] in ('auth','check') and s['status']=='failed'),None) if name=='databricks' else None
            caps.append(dict(schema_version=1,id=name,status='blocked' if failure else 'not_checked',reason=failure or reason,
                next_action='Observar la capacidad y adjuntar evidencia vigente',evidence=[]))
    admissible=['local_prepared'] if prepared else []
    local=next(c for c in caps if c['id']=='local')
    if local['status']=='available':
        receipt=json.loads(safe_path(local['evidence'][0]['evidence_path']).read_bytes())
        if receipt.get('baseline_clean') is True: admissible.append('local_clean')
    return SetupReport(schema_version=1,client_id=plan.inputs.binding.client_id,checkout_id=plan.inputs.binding.checkout_id,
        plan_sha256=plan.plan_sha256,prepared=prepared,stages=run.stages,capabilities=caps,
        hu_admissible=admissible)


def response(plan,run,**extra):
    reason=next((s['reason'] for s in run.stages if s['status']=='failed'),None)
    return result(status='blocked' if run.state=='failed' else 'prepared',reason=reason,report=capability_report(plan,run).model_dump(),**extra), ({'tool_unavailable':3,'auth_pending':3,'permission_conflict':3,'owned_resource_conflict':4,'plan_stale':4}.get(reason,6) if run.state=='failed' else 0)


def observe(plan,run,name,version,value,source='local_probe'):
    timestamp=datetime.now(timezone.utc)
    data=canonical(value)
    path=folder(plan)/(name+'-observation.json')
    # A new observation is immutable. Rechecks use a distinct receipt path.
    if path.exists(): path=folder(plan)/(name+'-'+uuid.uuid4().hex+'.json')
    run.owned[str(path)]=sha(data); persist(folder(plan)/'journal.json',run)
    with PinnedTree(path.parent) as tree:
        with tree.file(path.name,create=True) as handle: handle.write(data)
    run.observations[name]=dict(schema_version=1,id=name,status='available',reason=None,next_action=None,
        evidence=[dict(schema_version=1,identity=plan.inputs.binding.client_id+'/'+plan.inputs.binding.checkout_id,
            version=version,observed_at=timestamp.isoformat(),valid_until=(timestamp+timedelta(hours=24)).isoformat(),
            evidence_path=str(path),evidence_sha256=sha(data),source=source)])


def status(path):
    plan=select(path)
    if not (folder(plan)/'journal.json').exists():
        run=SetupJournal(schema_version=1,plan_sha256=plan.plan_sha256,parent_sha256=digest(path),target_identity='',
            child_path='',stages=[s.model_dump() for s in plan.stages],state='pending',owned={})
    else: run=journal(plan)
    return response(plan,run)


def persist_child(plan,run,content):
    out=Path(run.child_path)
    expected=sha(content)
    if out.exists():
        if digest(out)!=expected: raise ConfigError('owned_resource_conflict')
    else:
        run.owned[str(out)]=expected; persist(folder(plan)/'journal.json',run)
        with PinnedTree(out.parent) as tree:
            with tree.file(out.name,create=True) as handle: handle.write(content)
    run.owned[str(out)]=expected


@installed_operation
def apply(path,authorization,*,probe_fn=probe,recovering=False):
    plan=select(path,authorization); r=plan.inputs.guided_request; target=absolute_path(r.target_path)
    if not folder(plan).exists() and 'onboarding' in plan.child_payloads:
        old=GuidedOnboardingPlan.model_validate(json.loads(plan.child_payloads['onboarding']))
        guided.regenerate(old,probe_fn)
    state=ensure_state(plan.inputs.binding)
    with CheckoutLock(state,plan.run_id,recover=recovering):
        if not folder(plan).exists():
            with PinnedTree(state) as tree:
                with tree.directory('setup-'+plan.run_id,create=True): pass
            with PinnedTree(folder(plan)) as tree:
                with tree.file('owner.json',create=True) as handle: handle.write(canonical({'plan_sha256':plan.plan_sha256}))
        elif json.loads((folder(plan)/'owner.json').read_bytes())!={'plan_sha256':plan.plan_sha256}:
            raise ConfigError('owned_resource_conflict')
    with CheckoutLock(folder(plan),plan.run_id,recover=recovering):
        if not (folder(plan)/'journal.json').exists():
            # All target/input preconditions are checked before the first write.
            if 'onboarding' in plan.child_payloads:
                old=GuidedOnboardingPlan.model_validate(json.loads(plan.child_payloads['onboarding']))
                guided.regenerate(old,probe_fn)
            run=SetupJournal(schema_version=1,plan_sha256=plan.plan_sha256,parent_sha256=digest(path),
                target_identity='',child_path=str(Path(r.binding_path).with_name('setup-'+plan.run_id+'-child.json')),
                stages=[s.model_dump() for s in plan.stages],state='applying',owned={})
            persist(folder(plan)/'journal.json',run)
        else:
            run=journal(plan)
            if run.parent_sha256!=digest(path): raise ConfigError('plan_stale')
            if run.state=='failed' and not recovering: raise ConfigError('recovery_required')
            if run.state=='completed':
                child=guided.selected(run.child_path)
                guided.verify_prepared(child,guided.load_run(child),integrated=True)
                return response(plan,run,idempotent=True)
        for stage in run.stages:
            if stage['status']=='completed': continue
            select(path,authorization)
            name=stage['name']; run.state='applying'; stage['status']='pending'; persist(folder(plan)/'journal.json',run)
            try:
                checkpoint('before_'+name)
                if name=='tools':
                    from .setup_tools import prepare
                    tools,updated=prepare(json.loads(plan.child_payloads['tools']),folder(plan))
                    from .tool_runtime import refresh
                    refresh(tools)
                    if updated:
                        run.updated_installation_sha256=updated
                        run.owned[plan.inputs.installation_record]=updated
                        persist(folder(plan)/'journal.json',run)
                    install=record(plan)
                    if install:
                        for tool in install.tools:
                            if sha(safe_path(tool.path).read_bytes())!=tool.sha256: raise ConfigError('tool_unavailable')
                    # Verify versions before any selected binary can authenticate.
                    for tool in tools:
                        from .tool_runtime import compatible
                        if not compatible(tool.name,tool.version): raise ConfigError('tool_unavailable')
                        if tool.name=='python': continue
                        command=[tool.path,'--version']
                        if tool.name=='openspec':
                            node=next((t for t in tools if t.name=='node'),None)
                            if not node: raise ConfigError('tool_unavailable')
                            command=[node.path,tool.path,'--version']
                        check=subprocess.run(command,capture_output=True,timeout=30,env=dict(os.environ,OPENSPEC_TELEMETRY='0'))
                        if check.returncode or tool.version.encode() not in check.stdout or not compatible(tool.name,check.stdout.decode(errors='replace')): raise ConfigError('tool_unavailable')
                elif name=='checkout':
                    if plan.inputs.clone and not target.exists():
                        git=executable('git')
                        if not git: raise ConfigError('tool_unavailable')
                        completed=subprocess.run([git,'-c','core.hooksPath='+str(state/'disabled-hooks'),'clone','--branch',
                            plan.inputs.descriptor.base_branch,'--single-branch','--',plan.inputs.repository_url,str(target)],capture_output=True,timeout=120)
                        if completed.returncode: raise ConfigError('recovery_required')
                    with PinnedTree(target) as tree:
                        identity=tree.base.identity()
                        if run.target_identity and identity!=run.target_identity: raise ConfigError('owned_resource_conflict')
                        run.target_identity=identity
                    if 'onboarding' in plan.child_payloads:
                        content=plan.child_payloads['onboarding'].encode()
                    else:
                        child,_=guided.preview(request_draft(r),probe_fn=probe_fn)
                        generated=GuidedOnboardingPlan.model_validate(child['plan'])
                        from .setup_recipe import verify
                        verify(json.loads(plan.child_payloads['managed_recipe']),generated)
                        if generated.blockers: raise ConfigError('plan_stale')
                        content=canonical(generated.model_dump())
                    persist_child(plan,run,content)
                elif name=='prepare':
                    selected_installation=record(plan)
                    existing=[InstalledTool.model_validate(t) for t in json.loads(plan.child_payloads['tools'])['existing']]
                    tool_map={t.name:t for t in existing}
                    if selected_installation: tool_map.update({t.name:t for t in selected_installation.tools})
                    tools=list(tool_map.values())
                    if not any(t.name=='python' for t in tools):
                        tools=[*tools,*[InstalledTool.model_validate(t) for t in json.loads(plan.child_payloads['tools'])['existing'] if t['name']=='python']]
                    with using_tools(tools):
                        child=guided.selected(run.child_path)
                        if recovering and guided.folder(child).exists():
                            child_run=guided.load_run(child)
                            child_stage=guided.stage_record(child_run,'prepare')
                            if child_stage.status in ('failed','in_progress','conflict'):
                                _,code=guided.recover(run.child_path,stage='prepare',apply_changes=True)
                                if code: raise ConfigError('owned_resource_conflict')
                                child_run=guided.load_run(child)
                                guided.regenerate(child,probe_fn)
                                with CheckoutLock(guided.folder(child),child.run_id,recover=True):
                                    _,code=guided.prepare_stage(child,child_run)
                            else: _,code=guided.apply(run.child_path,stage='prepare',probe_fn=probe_fn)
                        else: _,code=guided.apply(run.child_path,stage='prepare',probe_fn=probe_fn)
                    if code: raise ConfigError('recovery_required')
                elif name=='integrate':
                    if recovering:
                        child=guided.selected(run.child_path); child_run=guided.load_run(child)
                        if guided.stage_record(child_run,'integrate').status in ('failed','in_progress','conflict'):
                            _,code=guided.recover(run.child_path,stage='integrate',apply_changes=True)
                            if code: raise ConfigError('owned_resource_conflict')
                    _,code=guided.apply(run.child_path,stage='integrate',probe_fn=probe_fn)
                    if code: raise ConfigError('recovery_required')
                    for op in plan.setup_operations:
                        selected=target/op.path
                        if selected.exists():
                            if digest(selected)!=op.sha256: raise ConfigError('owned_resource_conflict')
                        else:
                            run.owned[str(selected)]=op.sha256; persist(folder(plan)/'journal.json',run)
                            with PinnedTree(target) as tree:
                                with tree.file(op.path,create=True) as handle: handle.write(op.content.encode())
                    scope_path=Path(r.binding_path).with_name(Path(r.binding_path).name+'.setup.json')
                    content=canonical(plan.model_dump())
                    if scope_path.exists():
                        if digest(scope_path)!=sha(content): raise ConfigError('owned_resource_conflict')
                    else:
                        run.owned[str(scope_path)]=sha(content); persist(folder(plan)/'journal.json',run)
                        with PinnedTree(scope_path.parent) as tree:
                            with tree.file(scope_path.name,create=True) as handle: handle.write(content)
                    if plan.inputs.commit_local:
                        # Only the reviewed managed paths are staged. Hooks disabled;
                        # selected Git identity is required, no guessed user/email.
                        git=executable('git')
                        if not git: raise ConfigError('tool_unavailable')
                        indexed=git_read(target,'diff','--cached','--name-only','--no-ext-diff').splitlines()
                        if set(indexed)-set(plan.integration_writes): raise ConfigError('owned_resource_conflict')
                        for args in (['add','--',*plan.integration_writes],['commit','-m','Preparar Local-Harness desde plan revisado']):
                            check=subprocess.run([git,'-c','core.hooksPath='+str(state/'disabled-hooks'),'-C',str(target),*args],capture_output=True,timeout=30)
                            if check.returncode: raise ConfigError('owned_resource_conflict')
                elif name=='auth' and plan.inputs.remote_read:
                    # Login is interactive; native tooling owns credentials. Never
                    # store stdout/stderr or request secrets from the conversation.
                    tool=next((t for t in selected_tools(plan) if t.name=='databricks'),None)
                    if tool is None: raise ConfigError('tool_unavailable')
                    check=subprocess.run([tool.path,'auth','login','--host',plan.inputs.databricks_host,'--profile',plan.inputs.binding.databricks_profile],capture_output=True,timeout=120)
                    if check.returncode: raise ConfigError('auth_pending')
                elif name=='check':
                    child=guided.selected(run.child_path)
                    guided.verify_prepared(child,guided.load_run(child),integrated=True)
                    observe(plan,run,'local','0.1.0',dict(prepared=True,scope_sha256=sha(canonical(plan.inputs.access_scope.model_dump())),
                        baseline_clean=local_status(target).code=='clean'))
                    available_tools=selected_tools(plan)
                    if available_tools:
                        for tool in available_tools:
                            if tool.name=='python': continue
                            command=[tool.path,'--version']
                            if tool.name=='openspec':
                                node=next((t for t in available_tools if t.name=='node'),None)
                                if not node: raise ConfigError('tool_unavailable')
                                command=[node.path,tool.path,'--version']
                            check=subprocess.run(command,capture_output=True,timeout=30,env=dict(os.environ,OPENSPEC_TELEMETRY='0'))
                            if check.returncode or tool.version.encode() not in check.stdout: raise ConfigError('tool_unavailable')
                            if tool.name in ('git','openspec'): observe(plan,run,tool.name,tool.version,dict(path=tool.path,sha256=tool.sha256,version=tool.version))
                    if plan.inputs.remote_read:
                        tool=next(t for t in available_tools if t.name=='databricks')
                        check=subprocess.run([tool.path,'current-user','me','--profile',plan.inputs.binding.databricks_profile,'--output','json'],capture_output=True,timeout=30)
                        if check.returncode: raise ConfigError('permission_conflict')
                        # Retain a selected fact, never the raw auth response.
                        try: data=json.loads(check.stdout); identity=data.get('id')
                        except (ValueError,AttributeError): raise ConfigError('permission_conflict') from None
                        if not isinstance(identity,str): raise ConfigError('permission_conflict')
                        observe(plan,run,'databricks',tool.version,dict(id=identity,host=plan.inputs.databricks_host,profile=plan.inputs.binding.databricks_profile),source='remote_read')
                checkpoint('after_'+name)
                stage['status']='completed'; stage['reason']=None
                persist(folder(plan)/'journal.json',run)
            except (ConfigError,OSError,subprocess.SubprocessError) as error:
                stage['status']='failed'; stage['reason']=getattr(error,'code','recovery_required')
                if stage['reason'] not in ('invalid_input','identity_mismatch','access_denied','tool_unavailable','download_integrity_failed',
                    'skill_discovery_pending','auth_pending','permission_conflict','plan_stale','owned_resource_conflict','recovery_required','remote_not_checked'):
                    stage['reason']='recovery_required'
                run.state='failed'; persist(folder(plan)/'journal.json',run)
                if name in ('auth','check'): return response(plan,run,idempotent=False)
                raise ConfigError(stage['reason']) from None
        run.state='completed'; persist(folder(plan)/'journal.json',run)
        return response(plan,run,idempotent=False)


def recover(path,authorization,*,probe_fn=probe):
    return apply(path,authorization,probe_fn=probe_fn,recovering=True)
