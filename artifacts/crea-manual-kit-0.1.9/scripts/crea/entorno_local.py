"""Binding local opt-in. Solo resuelve identidad, nunca comandos ni permisos."""
import copy
from pathlib import Path

from team_common import read, safe_path


def binding(root, name='.crea/local.json'):
    if name != '.crea/local.json':
        raise ValueError('LOCAL_ENVIRONMENT_PATH_NOT_ALLOWED')
    path = safe_path(root, name)
    if path.exists() and path.stat().st_nlink != 1:
        raise ValueError('LOCAL_ENVIRONMENT_HARDLINK')
    data = read(path)
    if not isinstance(data, dict) or set(data) - {'schema_version', 'python_executable', 'databricks_profile'}:
        raise ValueError('LOCAL_ENVIRONMENT_UNKNOWN_FIELD')
    if data.get('schema_version') != '1.0':
        raise ValueError('LOCAL_ENVIRONMENT_VERSION')
    executable = data.get('python_executable')
    if not isinstance(executable, str) or not Path(executable).is_absolute() or not Path(executable).is_file():
        raise ValueError('LOCAL_INTERPRETER_REQUIRED')
    for parent in [Path(executable), *Path(executable).parents]:
        if parent.is_symlink() or getattr(parent, 'is_junction', lambda: False)():
            raise ValueError('LOCAL_INTERPRETER_LINK')
    profile = data.get('databricks_profile')
    if profile is not None and (not isinstance(profile, str) or not profile.strip()
                                or any(c in profile for c in '\r\n\0')):
        raise ValueError('LOCAL_PROFILE_INVALID')
    return data


def resolve(root, settings):
    effective = copy.deepcopy(settings)
    name = effective.pop('local_environment_path', None)
    if name is None:
        return effective
    if effective.get('python_executable') is not None:
        raise ValueError('CONFLICTING_INTERPRETER_SOURCES')
    effective['python_executable'] = binding(root, name)['python_executable']
    return effective


def databricks_profile(root, project):
    """Personal alias never changes the shared host/target or enables a capability."""
    local = safe_path(root, '.crea/local.json')
    return binding(root).get('databricks_profile') or project['databricks'].get('profile') if local.is_file() else project['databricks'].get('profile')
