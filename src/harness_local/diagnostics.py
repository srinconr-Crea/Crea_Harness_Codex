import json
import os
import re
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass, asdict
from importlib.resources import files
from pathlib import Path

import yaml

from harness_core.configuration import ConfigError, safe_path, read_bytes, load_document, validate_configuration

SKILLS = ('openspec-explore','openspec-propose','openspec-update-change','openspec-apply-change',
          'openspec-verify-change','openspec-sync-specs','openspec-archive-change')
MATRIX = json.loads(files('harness_local').joinpath('compatibility.json').read_text())['tools']
_AUTO = object()


@dataclass
class Check:
    id: str
    status: str
    code: str
    message: str
    observed_version: str | None = None
    remediation: str | None = None
    observed_branch: str | None = None


def aggregate(checks):
    if any(c.status in ('missing','unsupported','error') for c in checks):
        return 'blocked', 1
    return ('partial',0) if any(c.status=='not_checked' for c in checks) else ('ready',0)


def report(command, checks, **extra):
    status,code=aggregate(checks)
    return dict(schema_version=1,command=command,status=status,checks=[asdict(c) for c in checks],**extra),code


def run_bounded(argv, timeout=10, env=None, cwd=None):
    """Drain both pipes with a shared 64 KiB ceiling; never execute a shell."""
    try:
        process=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                 shell=False,env=env,cwd=cwd)
    except FileNotFoundError:
        raise ConfigError('tool_missing') from None
    except OSError:
        raise ConfigError('probe_failed') from None
    data=bytearray()
    lock=threading.Lock()
    exceeded=threading.Event()
    def consume(pipe):
        try:
            while chunk:=pipe.read(4096):
                with lock:
                    if len(data)+len(chunk)>65536:
                        exceeded.set()
                        process.kill()
                        return
                    data.extend(chunk)
        finally:
            pipe.close()
    threads=[threading.Thread(target=consume,args=(pipe,),daemon=True) for pipe in (process.stdout,process.stderr)]
    for thread in threads:
        thread.start()
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise ConfigError('probe_timeout') from None
    finally:
        for thread in threads:
            thread.join(timeout=1)
    if any(t.is_alive() for t in threads):
        raise ConfigError('probe_timeout')
    if exceeded.is_set():
        raise ConfigError('output_limit')
    if process.returncode:
        raise ConfigError('probe_failed')
    return data.decode('utf-8',errors='replace')


def launcher(name):
    executable=sys.executable if name=='python' else shutil.which(name)
    args=['-I','--version'] if name=='python' else ['--version']
    if executable and Path(executable).suffix.lower() in ('.cmd','.bat','.ps1'):
        if name!='openspec':
            return None,[], 'launcher_not_verified'
        entry=Path(executable).parent/'node_modules/@fission-ai/openspec/bin/openspec.js'
        node=shutil.which('node')
        if not node or not entry.is_file():
            return None,[], 'launcher_not_verified'
        return node,[str(entry),'--version'],None
    return executable,args,None


def probe(name, executable=_AUTO, args=None, timeout=10):
    if executable is _AUTO:
        executable,default,reason=launcher(name)
        if reason:
            return Check(name,'not_checked',reason,'La sonda requiere un launcher nativo verificado.')
        args=default
    if executable is None:
        return Check(name,'missing','tool_missing','Herramienta ausente.',remediation=f'Instalar la versión compatible de {name} por separado.')
    try:
        env=dict(os.environ,OPENSPEC_TELEMETRY='0',GIT_OPTIONAL_LOCKS='0')
        output=run_bounded([executable,*(args if args is not None else ['--version'])],timeout,env=env,cwd=os.path.dirname(sys.executable))
        match=re.search(r'(?<![\w])v?(\d+)\.(\d+)(?:\.(\d+))?',output)
        if not match:
            raise ConfigError('version_unrecognized')
        version=tuple(int(x or 0) for x in match.groups())
        rules=MATRIX[name]
        compatible=(version>=tuple(rules.get('minimum',[0,0,0])) and
                    ('exclusive_maximum' not in rules or version<tuple(rules['exclusive_maximum'])) and
                    ('exact' not in rules or version==tuple(rules['exact'])))
        return Check(name,'ready' if compatible else 'unsupported','compatible' if compatible else 'version_unsupported',
                     'Versión local compatible.' if compatible else 'Versión fuera de la matriz del kit.', '.'.join(map(str,version)))
    except ConfigError as error:
        return Check(name,'missing' if error.code=='tool_missing' else 'error',error.code,'No se pudo completar la sonda local.')


def git_read(target, *args, overrides=()):
    executable=shutil.which('git')
    if not executable:
        raise ConfigError('tool_missing')
    env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull)
    # Disable optional external monitoring and isolate from inherited git-directory overrides.
    for key in ('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE','GIT_COMMON_DIR'):
        env.pop(key,None)
    return run_bounded([executable,'-c','core.fsmonitor=false',*overrides,'-C',str(target),*args],env=env).strip()


def local_status(target):
    # `status` may run clean/process filters while refreshing tracked content.
    # Discover names only, never execute or display configured commands.
    try:
        keys=git_read(target,'config','--name-only','--get-regexp',r'^filter\.').splitlines()
    except ConfigError as error:
        if error.code!='probe_failed':
            raise
        keys=[]
    overrides=[]
    for key in keys:
        match=re.fullmatch(r'filter\.([A-Za-z0-9_.-]+)\.[A-Za-z0-9_-]+',key)
        if not match:
            return Check('git_status','not_checked','filter_not_verified','Filtro Git con nombre no admitido; estado pendiente.')
        for suffix,value in (('clean',''),('process',''),('required','false')):
            overrides.extend(['-c',f'filter.{match.group(1)}.{suffix}={value}'])
    dirty=bool(git_read(target,'status','--porcelain','--untracked-files=normal',overrides=overrides))
    return Check('git_status','ready','dirty' if dirty else 'clean','Cambios locales presentes.' if dirty else 'Checkout limpio.')


def checkout(target):
    target=safe_path(target)
    if not target.is_dir():
        raise ConfigError('target_not_found')
    try:
        root=git_read(target,'rev-parse','--show-toplevel')
    except ConfigError as error:
        if error.code=='probe_failed':
            raise ConfigError('not_git_checkout') from None
        raise
    if Path(root).resolve()!=target:
        raise ConfigError('not_git_checkout')
    try:
        origin=git_read(target,'remote','get-url','origin')
    except ConfigError as error:
        if error.code!='probe_failed':
            raise
        origin=None
    return target,origin


def inspect_target(target, openspec_root='openspec'):
    target,_=checkout(target)
    checks=[Check('git_checkout','ready','git_checkout','Checkout Git válido.')]
    try:
        branch=git_read(target,'symbolic-ref','--quiet','--short','HEAD')
    except ConfigError as error:
        if error.code!='probe_failed':
            raise
        branch=''
    # The branch is client input; report a sanitized shape rather than arbitrary terminal text.
    from harness_core.configuration import reject_secrets
    try:
        reject_secrets(branch)
        observed=branch if re.fullmatch(r'[A-Za-z0-9_./-]{1,200}',branch) else None
    except ConfigError:
        observed=None
    checks.append(Check('git_branch','ready','branch_observed' if branch else 'detached','Rama local observada.' if branch else 'HEAD separado.',observed_branch=observed))
    checks.append(local_status(target))
    config=target/openspec_root/'config.yaml'
    if not safe_path(config).exists():
        checks.append(Check('openspec_config','missing','file_missing','Falta configuración OpenSpec.',remediation='Preparar OpenSpec en un cambio revisado.'))
    else:
        value=load_document(config)
        checks.append(Check('openspec_config','ready' if value.get('schema')=='spec-driven' else 'unsupported',
                            'compatible' if value.get('schema')=='spec-driven' else 'schema_unsupported','Configuración OpenSpec inspeccionada.'))
    for name in SKILLS:
        path=target/'.agents/skills'/name/'SKILL.md'
        if not safe_path(path).exists():
            checks.append(Check(name,'missing','skill_missing','Falta workflow OpenSpec.',remediation='Preparar los siete workflows aprobados.'))
            continue
        try:
            text=read_bytes(path).decode('utf-8-sig')
            match=re.match(r'^---\s*\r?\n(.*?)\r?\n---(?:\r?\n|$)',text,re.S)
            # Parse only frontmatter, with the same bounded and duplicate-key-safe loader.
            from harness_core.configuration import UniqueLoader, reject_secrets
            data=yaml.load(match.group(1),Loader=UniqueLoader) if match else None
            reject_secrets(data)
            compatible=isinstance(data,dict) and data.get('name')==name and isinstance(data.get('metadata'),dict) and str(data['metadata'].get('generatedBy'))=='1.13.2'
        except (ValueError,TypeError,yaml.YAMLError,RecursionError):
            compatible=False
        checks.append(Check(name,'ready' if compatible else 'unsupported','compatible' if compatible else 'skill_incompatible','Metadatos del workflow inspeccionados.'))
    codex=safe_path(target/'.codex/config.toml')
    checks.append(Check('codex_files','not_checked','present' if codex.exists() else 'absent','Presencia de configuración observada; requiere revisión en Desktop.'))
    return checks


def doctor(target=None,policy=None,binding=None,probe_fn=probe):
    checks=[probe_fn(name) for name in MATRIX]
    if (policy is None)!=(binding is None):
        raise ConfigError('configuration_flags_incomplete')
    if target:
        descriptor_path=safe_path(Path(target)/'.harness/client.yaml')
        from harness_core.contracts import Descriptor
        descriptor=load_document(descriptor_path,Descriptor) if descriptor_path.exists() else None
        checks.extend(inspect_target(target,descriptor.openspec_root if descriptor else 'openspec'))
        if policy:
            _,origin=checkout(target)
            validate_configuration(target,policy,binding,origin)
            checks.append(Check('client_configuration','ready','configuration_valid','Descriptor, política y binding coherentes.'))
    elif policy:
        raise ConfigError('target_required')
    if not policy:
        checks.append(Check('client_configuration','not_checked','configuration_not_supplied','Validación operativa pendiente.'))
    checks.extend([Check('desktop_capabilities','not_checked','desktop_not_verified','Skills, agentes, modelos y hooks requieren prueba en Desktop.'),
                   Check('databricks_auth','not_checked','auth_not_verified','Autenticación y acceso remoto no comprobados.')])
    return report('doctor',checks)
