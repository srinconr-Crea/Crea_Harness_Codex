"""Primitivas de equipo: biblioteca estándar, rutas acotadas y argv sin shell."""
import json
import os
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone

from testing.common import read, safe_path, digest, file_hash

CONTRACTS = {'kit': '0.1.9', 'delivery_target': '1.0', 'local_environment': '1.0',
             'target_compatibility': '1.0', 'projection': 'content-v3'}


def utc():
    return datetime.now(timezone.utc).isoformat()


def identity(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', value):
        raise ValueError('SAFE_CHANGE_AND_ATTEMPT_REQUIRED')
    return value


def redact(value):
    value = re.sub(r'https?://[^/@\s]+:[^/@\s]+@', 'https://[REDACTED]@', str(value))
    value = re.sub(r'(?i)(token|password|secret|api[_-]?key)\s*[=:]\s*\S+', r'\1=[REDACTED]', value)
    return re.sub(r'(?i)Bearer\s+\S+', 'Bearer [REDACTED]', value)


def process(argv, root=None, timeout=30, env=None):
    actual = dict(os.environ if env is None else env)
    actual.update({'GIT_TERMINAL_PROMPT': '0', 'GCM_INTERACTIVE': 'never', 'GIT_NO_LAZY_FETCH': '1', 'GIT_OPTIONAL_LOCKS':'0',
                   'AZURE_EXTENSION_USE_DYNAMIC_INSTALL': 'no', 'PYTHONDONTWRITEBYTECODE': '1'})
    return subprocess.run(argv, cwd=root, capture_output=True, timeout=timeout, env=actual,
                          shell=False, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)


def git_result(root, *args):
    return process(['git', '-c', 'core.quotepath=false', '-c', 'core.fsmonitor=false',
                    '-c', 'credential.interactive=false', *args], root)


def git(root, *args):
    result = git_result(root, *args)
    if result.returncode:
        raise ValueError('GIT_OPERATION_FAILED: ' + args[0])
    return result.stdout.decode('utf-8', errors='strict').strip()


def exclusive(root, name, data, prefix):
    if not name.startswith(prefix):
        raise ValueError('OUTPUT_OUTSIDE_ALLOWED_DIRECTORY')
    path = safe_path(root, name)
    if path.exists():
        raise ValueError('OUTPUT_ALREADY_EXISTS')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    return {'path': name, 'sha256': file_hash(path)}


def hu_export(root, name, data, change):
    return exclusive(root, name, data, 'docs/hu/' + identity(change) + '/compatibilidad/')


def validate_data(root, schema_name, data):
    from testing.schemas import validate_schema
    return validate_schema(read(safe_path(root, schema_name)), data)
