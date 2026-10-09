import hashlib
import json
from importlib.resources import files

from harness_core.configuration import ConfigError, load_document, digest, read_bytes, safe_path, validate_configuration
from harness_core.contracts import Descriptor, Policy
from .diagnostics import checkout, inspect_target, report, probe, MATRIX


def preview(target,policy_path,binding_path,repo=None,base_branch=None,probe_fn=probe):
    target,origin=checkout(target)
    policy=load_document(policy_path,Policy)
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
    config=validate_configuration(target,policy_path,binding_path,origin,descriptor=descriptor)
    checks=[probe_fn(name) for name in MATRIX]+inspect_target(target,descriptor.openspec_root)
    actions=[]
    hashes={'policy':digest(policy_path),'binding':digest(binding_path)}
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
            action('openspec','existing' if check.status=='ready' else ('manual' if check.status=='missing' else 'conflict'),
                   rel,'Preservar compatible; preparar o revisar los elementos pendientes.')
    codex=safe_path(target/'.codex/config.toml')
    if codex.exists():
        hashes['.codex/config.toml']=digest(codex)
    action('desktop','manual','.codex/config.toml','Revisar configuración y confianza en Desktop; no generar agentes ni hooks.')
    action('authentication','manual',None,'Autenticación Databricks futura, separada y autorizada.')
    actions.sort(key=lambda a:(a['kind'],a['path'] or '',a['status']))
    result,code=report('init',checks,identities={'client_id':descriptor.client_id,'checkout_id':config['binding'].checkout_id,
        'repository':descriptor.repository,'base_branch':descriptor.base_branch},input_hashes=dict(sorted(hashes.items())),actions=actions)
    if any(a['status']=='conflict' for a in actions):
        result['status'],code='blocked',1
    return result,code
