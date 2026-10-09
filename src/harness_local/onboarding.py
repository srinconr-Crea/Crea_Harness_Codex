import hashlib
import json
from importlib.resources import files

from harness_core.configuration import ConfigError, load_document, digest, read_bytes, safe_path, validate_configuration
from harness_core.contracts import Descriptor, Policy, Binding
from harness_core.onboarding_plan import OnboardingPlan, Operation, canonical, sha, authorize, absolute_path, separate, unmanaged_path
from .diagnostics import checkout, inspect_target, report, probe, MATRIX, Check
from .resources import kit
from .windows_fs import PinnedTree


def preview(target,policy_path,binding_path=None,repo=None,base_branch=None,probe_fn=probe,
            *,binding_out=None,checkout_id=None,state_dir=None,databricks_profile=None,plan_out=None):
    target,origin=checkout(target)
    policy=load_document(policy_path,Policy)
    policy_path=absolute_path(str(safe_path(policy_path)))
    proposed=None
    if binding_out:
        if binding_path or not checkout_id or not state_dir:
            raise ConfigError('binding_inputs_invalid')
        binding_path=unmanaged_path(binding_out)
        if binding_path.exists():
            raise ConfigError('binding_exists')
        try:
            proposed=Binding(schema_version=1,client_id=policy.client_id,checkout_id=checkout_id,
                target_path=str(target),policy_sha256=digest(policy_path),state_dir=str(unmanaged_path(state_dir)),
                databricks_profile=databricks_profile)
        except ConfigError:
            raise
        except ValueError:
            raise ConfigError('binding_inputs_invalid') from None
    elif not binding_path or any(x is not None for x in (checkout_id,state_dir,databricks_profile)):
        raise ConfigError('binding_inputs_invalid')
    binding_path=absolute_path(str(safe_path(binding_path)))
    path=safe_path(target/'.harness/client.yaml')
    exists=path.exists()
    if exists:
        descriptor=load_document(path,Descriptor)
        if (repo is not None and repo.lower()!=descriptor.repository.lower()) or (base_branch is not None and base_branch!=descriptor.base_branch):
            raise ConfigError('descriptor_input_conflict')
    else:
        if not repo or not base_branch:
            raise ConfigError('descriptor_input_required')
        try:
            descriptor=Descriptor(schema_version=1,client_id=policy.client_id,repository=repo,base_branch=base_branch)
        except ValueError:
            raise ConfigError('invalid_descriptor_input') from None
    config=validate_configuration(target,policy_path,binding_path,origin,descriptor=descriptor,proposed_binding=proposed)
    separate([str(target),str(policy_path),str(binding_path),config['binding'].state_dir])
    resources,manifest_hash=kit()
    checks=[probe_fn(name) for name in MATRIX]+inspect_target(target,descriptor.openspec_root)
    actions=[]
    binding_content=json.dumps(config['binding'].model_dump(),ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    hashes={'policy':digest(policy_path),'binding':sha(binding_content.encode('utf-8')) if proposed else digest(binding_path)}
    def action(kind,status,path,reason,content=None):
        item=dict(kind=kind,status=status,path=path,reason=reason)
        if content is not None:
            item.update(content=content,sha256=hashlib.sha256(content.encode('utf-8')).hexdigest())
        actions.append(item)
    if exists:
        hashes['descriptor']=digest(path)
        action('descriptor','existing','.harness/client.yaml','Preservar descriptor validado.')
    else:
        content=json.dumps(descriptor.model_dump(),ensure_ascii=False,sort_keys=True,indent=2)+'\n'
        action('descriptor','proposed','.harness/client.yaml','Crear después de revisar el preview.',content)
    instructions=files('harness_local').joinpath('templates/AGENTS.md').read_text(encoding='utf-8')
    agents=safe_path(target/'AGENTS.md')
    if agents.exists():
        hashes['AGENTS.md']=digest(agents)
        equal=read_bytes(agents).decode('utf-8-sig').replace('\r\n','\n')==instructions.replace('\r\n','\n')
        action('instructions','existing' if equal else 'conflict','AGENTS.md','Preservar; integrar manualmente si difiere.',instructions if not equal else None)
    else:
        action('instructions','proposed','AGENTS.md','Instrucciones genéricas revisables.',instructions)
    for check in checks:
        if check.id=='openspec_config' or check.id.startswith('openspec-'):
            rel=f'{descriptor.openspec_root}/config.yaml' if check.id=='openspec_config' else f'.agents/skills/{check.id}/SKILL.md'
            p=safe_path(target/rel)
            if p.exists():
                hashes[rel]=digest(p)
            resource='openspec/config.yaml' if check.id=='openspec_config' else rel
            action('openspec','existing' if check.status=='ready' else ('proposed' if check.status=='missing' else 'conflict'),
                   rel,'Preservar compatible; preparar o revisar los elementos pendientes.',
                   resources[resource] if check.status=='missing' else None)
    codex=safe_path(target/'.codex/config.toml')
    if codex.exists():
        hashes['.codex/config.toml']=digest(codex)
    action('desktop','manual','.codex/config.toml','Revisar configuración y confianza en Desktop; no generar agentes ni hooks.')
    action('authentication','manual',None,'Autenticación Databricks futura, separada y autorizada.')
    if proposed:
        action('binding','proposed',str(binding_path),'Binding explícito del desarrollador.',binding_content)
    actions.sort(key=lambda a:(a['kind'],a['path'] or '',a['status']))
    result,code=report('init',checks,identities={'client_id':descriptor.client_id,'checkout_id':config['binding'].checkout_id,
        'repository':descriptor.repository,'base_branch':descriptor.base_branch},input_hashes=dict(sorted(hashes.items())),actions=actions)
    if any(a['status']=='conflict' for a in actions):
        result['status'],code='blocked',1
    operations=[Operation(schema_version=1,scope='binding' if a['kind']=='binding' else 'target',
        path=a['path'],content=a['content'],sha256=a['sha256']) for a in actions if a['status']=='proposed']
    # The binding is committed only after every client file.
    operations.sort(key=lambda o:(o.scope=='binding',o.path.lower()))
    denied_code=authorize(operations,policy)
    if denied_code:
        result['checks'].append(vars(Check('policy','error',denied_code,'La política no autoriza estas creaciones.')))
        result['status'],code='blocked',1
    applicable=not denied_code and not any(a['status']=='conflict' for a in actions)
    applicable=applicable and all(c.status=='ready' for c in checks if c.id in ('python','git'))
    payload=dict(schema_version=1,kind='onboarding_plan',kit_version='0.1.0',resource_manifest_sha256=manifest_hash,
        target_path=str(target),origin=origin,policy_path=str(policy_path),policy_sha256=digest(policy_path),
        binding_path=str(binding_path),binding_mode='proposed' if proposed else 'existing',
        binding=config['binding'].model_dump(),descriptor=descriptor.model_dump(),input_hashes=dict(sorted(hashes.items())),
        absent_paths=sorted(o.path for o in operations if o.scope=='target'),applicable=bool(applicable),
        operations=[o.model_dump() for o in operations])
    plan=OnboardingPlan.model_validate(dict(payload,plan_sha256=sha(canonical(payload))))
    result.update(applicable=bool(applicable),plan=plan.model_dump())
    if plan_out is not None:
        out=unmanaged_path(plan_out)
        separate([str(out),str(target),str(policy_path),str(binding_path),config['binding'].state_dir])
        if out.exists():
            raise ConfigError('export_exists')
        with PinnedTree(out.parent) as tree:
            with tree.file(out.name,create=True) as handle:
                handle.write(canonical(plan.model_dump())+b'\n')
    return result,code
