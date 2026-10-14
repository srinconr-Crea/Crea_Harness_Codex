"""Prepare missing selected tools from the approved offline installation closure."""
import json
from contextlib import ExitStack
from pathlib import Path
import subprocess
import zipfile

from harness_core.configuration import ConfigError,safe_path
from harness_core.onboarding_plan import canonical,sha,destination_path,load_json
from harness_core.setup import InstallationRecord,InstalledTool
from .installation import validate_kit
from .execution_state import CheckoutLock,persist
from .windows_fs import PinnedTree


def plan_tools(inputs,existing):
    names={'git'}
    if 'openspec' in inputs.capabilities: names.update(('node','openspec'))
    if 'databricks' in inputs.capabilities: names.add('databricks')
    selected={t.name:t for t in existing}
    missing=sorted(names-set(selected))
    record=load_json(inputs.installation_record,InstallationRecord,limit=8*1024*1024) if inputs.installation_record else None
    kit=inputs.installation_kit or (record.kit_path if record else None)
    operations=[]; blocked=False
    if missing:
        if not record or not kit: blocked=True
        else:
            manifest=validate_kit(kit)
            for name in missing:
                tool=manifest['tools'][name]
                destination=safe_path(Path(record.installation_root)/('tools-'+name+'-'+tool['version']))
                if destination.exists(): raise ConfigError('owned_resource_conflict')
                operations.append(dict(name=name,version=tool['version'],license=tool['license'],artifact=str(Path(kit)/tool['artifact']),
                    sha256=tool['sha256'],destination=str(destination),binary=tool['binary'],kind='self_extract' if name=='git' else 'zip'))
    return dict(existing=[t.model_dump() for t in existing],operations=operations,blocked=blocked,
        installation_record=inputs.installation_record,kit_path=kit,kit_sha256=sha((Path(kit)/'install-manifest.json').read_bytes()) if kit else None)


class Receipt:
    def __init__(self,value): self.value=value
    def model_dump(self): return self.value


def mkdir(tree,relative):
    parts=relative.split('/')
    for i in range(1,len(parts)+1):
        path='/'.join(parts[:i])
        try:
            with tree.directory(path,create=True): pass
        except ConfigError as error:
            if error.code!='destination_exists': raise
            with tree.directory(path): pass


def prepare(recipe, journal_dir):
    tools=[InstalledTool.model_validate(t) for t in recipe['existing']]
    if recipe['blocked']: raise ConfigError('tool_unavailable')
    if not recipe['operations']: return tools,None
    if sha((safe_path(recipe['kit_path'])/'install-manifest.json').read_bytes())!=recipe['kit_sha256']:
        raise ConfigError('plan_stale')
    manifest=validate_kit(recipe['kit_path'])
    record_path=safe_path(recipe['installation_record'])
    record=load_json(record_path,InstallationRecord,limit=8*1024*1024)
    root=safe_path(record.installation_root)
    # Verify every conditional destination before executing even a self-extractor.
    for op in recipe['operations']:
        if set(op)!={'name','version','license','artifact','sha256','destination','binary','kind'} or op['name'] not in manifest['tools']:
            raise ConfigError('invalid_input')
        approved=manifest['tools'][op['name']]
        expected=dict(name=op['name'],version=approved['version'],license=approved['license'],
            artifact=str(Path(recipe['kit_path'])/approved['artifact']),sha256=approved['sha256'],
            destination=str(root/('tools-'+op['name']+'-'+approved['version'])),binary=approved['binary'],
            kind='self_extract' if op['name']=='git' else 'zip')
        if op!=expected: raise ConfigError('plan_stale')
    log_path=journal_dir/'tools-journal.json'
    log={'schema_version':1,'recipe_sha256':sha(canonical(recipe)),'root_identity':None,'state':'prepared','completed':{},'records':{}}
    if log_path.exists():
        saved=json.loads(log_path.read_bytes())
        if saved['recipe_sha256']!=log['recipe_sha256']: raise ConfigError('owned_resource_conflict')
        log=saved
    with ExitStack() as artifacts,CheckoutLock(root,'setup-tools',recover=True),PinnedTree(root) as tree:
        kit_tree=artifacts.enter_context(PinnedTree(recipe['kit_path']))
        manifest_handle=artifacts.enter_context(kit_tree.verified_binary('install-manifest.json'))
        if sha(manifest_handle.read(8*1024*1024))!=recipe['kit_sha256']: raise ConfigError('plan_stale')
        if log['root_identity'] and log['root_identity']!=tree.base.identity(): raise ConfigError('owned_resource_conflict')
        log['root_identity']=tree.base.identity(); persist(log_path,Receipt(log))
        for op in recipe['operations']:
            source=safe_path(op['artifact']); destination=safe_path(op['destination'])
            approved=manifest['tools'][op['name']]
            if (approved['version'],approved['sha256'],approved['binary'])!=(op['version'],op['sha256'],op['binary']):
                raise ConfigError('plan_stale')
            source_handle=artifacts.enter_context(kit_tree.verified_binary(approved['artifact']))
            if sha(source_handle.read(1024*1024*1024))!=op['sha256']: raise ConfigError('download_integrity_failed')
            if op['name'] in log['completed']:
                existing=InstalledTool.model_validate(log['completed'][op['name']])
                if sha(safe_path(existing.path).read_bytes())!=existing.sha256: raise ConfigError('owned_resource_conflict')
                tools.append(existing); continue
            if destination.exists(): raise ConfigError('recovery_required')
            relative=destination.relative_to(root).as_posix(); destination_path(relative)
            log['state']='installing'; log['records'][relative]={'state':'planned'}; persist(log_path,Receipt(log))
            if op['kind']=='self_extract':
                check=subprocess.run([str(source),'-y','-o'+str(destination)],capture_output=True,timeout=120,
                    creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                if check.returncode: raise ConfigError('recovery_required')
            else:
                with zipfile.ZipFile(source) as archive:
                    entries=[e for e in archive.infolist() if not e.is_dir()]
                    names=[e.filename.casefold() for e in entries]
                    if len(names)>8192 or len(set(names))!=len(names) or sum(e.file_size for e in entries)>1024*1024*1024:
                        raise ConfigError('download_integrity_failed')
                    for entry in entries:
                        destination_path(entry.filename)
                        if (entry.external_attr>>16)&0xf000==0xa000: raise ConfigError('download_integrity_failed')
                    mkdir(tree,relative)
                    for entry in entries:
                        selected=relative+'/'+entry.filename
                        parent=selected.rsplit('/',1)[0]; mkdir(tree,parent)
                        data=archive.read(entry)
                        log['records'][selected]={'state':'planned','sha256':sha(data)}; persist(log_path,Receipt(log))
                        with tree.file(selected,create=True) as handle:
                            handle.write(data); log['records'][selected].update(state='created',identity=handle.identity())
                        persist(log_path,Receipt(log))
            for file in destination.rglob('*'):
                file=safe_path(file)
                if file.is_file(): record.owned_files[file.relative_to(root).as_posix()]=sha(file.read_bytes())
            binary=safe_path(destination/op['binary'])
            installed=InstalledTool(schema_version=1,name=op['name'],version=op['version'],path=str(binary),sha256=sha(binary.read_bytes()),license=op['license'])
            tools.append(installed); log['completed'][op['name']]=installed.model_dump(); persist(log_path,Receipt(log))
        previous={t.name:t for t in record.tools}; previous.update({t.name:t for t in tools if t.name!='python'})
        record.tools=list(previous.values()); record.kit_path=recipe['kit_path']
        # Only the registry changes; runtime, Skills and client evidence remain.
        persist(record_path,record)
        log['state']='completed'; persist(log_path,Receipt(log))
    return tools,sha(record_path.read_bytes())
