"""Absolute verified tools scoped to one operation, never a PATH mutation."""
from contextlib import contextmanager, ExitStack
from contextvars import ContextVar

from harness_core.configuration import ConfigError, safe_path
from harness_core.onboarding_plan import sha
from .windows_fs import PinnedTree

_TOOLS=ContextVar('harness_selected_tools',default=None)
_STACK=ContextVar('harness_tool_handles',default=None)


def override(name):
    values=_TOOLS.get()
    if values is None: return None
    return values.get(name,(None,None,'tool_missing'))


def executable(name):
    selected=override(name)
    if selected is None:
        import shutil
        return shutil.which(name)
    return selected[0]


def compatible(name,version):
    import re
    from .diagnostics import MATRIX
    match=re.search(r'\d+\.\d+(?:\.\d+)?',version)
    if name not in MATRIX or not match: return False
    parts=tuple(map(int,match[0].split('.'))); parts=parts+(0,)*(3-len(parts))
    rules=MATRIX[name]
    return (parts>=tuple(rules.get('minimum',[0,0,0])) and
        ('exclusive_maximum' not in rules or parts<tuple(rules['exclusive_maximum'])) and
        ('exact' not in rules or parts==tuple(rules['exact'])))


def discover(record=None, required=None):
    """Read/probe compatible native tools once; the parent freezes these paths."""
    import re,shutil,subprocess,sys
    from pathlib import Path
    from harness_core.setup import InstalledTool
    tools={t.name:t for t in record.tools if compatible(t.name,t.version) and (required is None or t.name in required)} if record else {}
    runtime=record.runtime_path if record else sys.executable
    tools['python']=InstalledTool(schema_version=1,name='python',version='3.13',path=runtime,
        sha256=sha(safe_path(runtime).read_bytes()),license='PSF')
    for name,license in (('git','GPL-2.0'),('node','MIT'),('databricks','Databricks License')):
        if required is not None and name not in required: continue
        if name in tools: continue
        path=shutil.which(name)
        if not path or Path(path).suffix.lower()!='.exe': continue
        with PinnedTree(Path(path).parent) as tree:
            with tree.verified_binary(Path(path).name) as handle:
                expected=sha(handle.read(256*1024*1024))
                checked=subprocess.run([path,'--version'],capture_output=True,timeout=10)
                match=re.search(rb'\d+\.\d+\.\d+',checked.stdout)
                if checked.returncode or not match: continue
                if not compatible(name,match[0].decode()): continue
                tools[name]=InstalledTool(schema_version=1,name=name,version=match[0].decode(),path=path,sha256=expected,license=license)
    return list(tools.values())


@contextmanager
def using_tools(tools):
    from types import SimpleNamespace
    runtime=next(t.path for t in tools if t.name=='python')
    with installation_tools(SimpleNamespace(runtime_path=runtime,tools=tools)):
        yield


@contextmanager
def installation_tools(record):
    if record is None:
        yield
        return
    values={'python':(record.runtime_path,['--version'],None)}
    with ExitStack() as stack:
        stack_token=_STACK.set(stack)
        stack.callback(_STACK.reset,stack_token)
        for tool in record.tools:
            path=safe_path(tool.path)
            tree=stack.enter_context(PinnedTree(path.parent))
            handle=stack.enter_context(tree.verified_binary(path.name))
            if sha(handle.read(256*1024*1024))!=tool.sha256: raise ConfigError('owned_resource_conflict')
            values[tool.name]=(str(path),['--version'],None)
        if 'openspec' in values:
            if 'node' not in values: raise ConfigError('tool_unavailable')
            values['openspec']=(values['node'][0],[values['openspec'][0],'--version'],None)
        token=_TOOLS.set(values)
        try: yield
        finally:
            _TOOLS.reset(token)


def refresh(tools):
    """Pin newly prepared binaries in the current operation's existing lease."""
    stack=_STACK.get(); values=_TOOLS.get()
    if stack is None or values is None: raise ConfigError('tool_unavailable')
    for tool in tools:
        path=safe_path(tool.path)
        tree=stack.enter_context(PinnedTree(path.parent)); handle=stack.enter_context(tree.verified_binary(path.name))
        if sha(handle.read(256*1024*1024))!=tool.sha256: raise ConfigError('owned_resource_conflict')
        values[tool.name]=(str(path),['--version'],None)
    by_name={t.name:t for t in tools}
    if 'openspec' in by_name:
        if 'node' not in by_name: raise ConfigError('tool_unavailable')
        values['openspec']=(by_name['node'].path,[by_name['openspec'].path,'--version'],None)
