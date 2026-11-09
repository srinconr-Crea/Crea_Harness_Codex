"""Read-only portable AI Tools inventory. No installer, authentication or network."""
import hashlib
import json
import os
from pathlib import Path
import re


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def confined(root, path):
    root, path = Path(root).resolve(), Path(path).absolute()
    try:
        path.relative_to(root)
        path.resolve().relative_to(root)
    except ValueError:
        raise ValueError('PATH_OUTSIDE_PROJECT') from None
    for ancestor in [path, *path.parents]:
        if ancestor == root.parent:
            break
        if ancestor.is_symlink() or (hasattr(ancestor, 'is_junction') and ancestor.is_junction()):
            raise ValueError('LINK_NOT_ALLOWED')
    return path


def scan_surface(path):
    """Read every discovered frontmatter identity; inaccessible trees are unknown."""
    path = Path(path)
    if not path.exists():
        return []
    result = []
    def visit(directory):
        with os.scandir(directory) as entries:
            entries = sorted(entries, key=lambda item: item.name)
        for entry in entries:
            if entry.is_symlink():
                raise OSError('LINKED_SKILL_SURFACE')
            if entry.is_dir(follow_symlinks=False):
                visit(Path(entry.path))
            elif entry.name == 'SKILL.md':
                skill = Path(entry.path)
                text = skill.read_text(encoding='utf-8-sig')
                front = text.split('---', 2)
                match = re.search(r'^name:\s*[\'"]?([^\r\n\'"]+)', front[1], re.M) if len(front) == 3 and not front[0].strip() else None
                if not match:
                    raise ValueError('INVALID_SKILL_FRONTMATTER: ' + str(skill))
                hashes = []
                for current, dirs, files in os.walk(skill.parent, followlinks=False, onerror=lambda error: (_ for _ in ()).throw(error)):
                    dirs[:] = sorted(d for d in dirs if d not in {'__pycache__', '.git'})
                    for name in sorted(files):
                        item = Path(current) / name
                        if item.is_symlink():
                            raise OSError('LINKED_SKILL_FILE')
                        hashes.append([item.relative_to(skill.parent).as_posix(), digest(item)])
                result.append({'name': match.group(1).strip(), 'path': str(skill), 'sha256': digest(skill),
                               'tree_sha256': hashlib.sha256(json.dumps(hashes).encode()).hexdigest()})
    visit(path)
    return result


def export_new(report, out, project_root):
    path = confined(project_root, out)
    if not path.parent.is_dir():
        raise ValueError('OUTPUT_PARENT_MISSING')
    # Exclusive creation is the only optional preview write; no mkdir or overwrite.
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def validate_lock(root, lock):
    issues = []
    if not re.fullmatch(r'[0-9a-f]{40}', str(lock.get('revision', ''))):
        issues.append({'code': 'IMMUTABLE_REVISION_MISSING'})
    for entry in lock.get('files', []):
        try:
            path = confined(root, Path(root) / entry['path'])
            if not path.is_file() or digest(path) != entry['distributed_sha256']:
                issues.append({'code': 'LOCKED_RESOURCE_MISSING_OR_CHANGED', 'path': entry['path']})
        except (OSError, ValueError, KeyError):
            issues.append({'code': 'INVALID_LOCKED_RESOURCE', 'path': entry.get('path')})
    return issues


def preview(config_path, *, kit_root=None, lock=None, surfaces=None):
    config_path = Path(config_path).resolve()
    read_json(config_path)  # Validate input; setup booleans never authorize hook execution.
    project_root = config_path.parent.parent
    kit_root = Path(kit_root) if kit_root is not None else Path(__file__).resolve().parents[2]
    if lock is None:
        lock = read_json(kit_root / 'resources/databricks-aitools/upstream-lock.json')
    issues = validate_lock(kit_root, lock)
    selection = lock.get('selected_skills', [])
    if len(selection) != len(set(selection)):
        issues.append({'code': 'DUPLICATE_SELECTED_IDENTITY'})
    try:
        bundled = scan_surface(kit_root / '.agents/skills')
    except (OSError, ValueError) as error:
        bundled = []
        issues.append({'code': 'BUNDLED_SURFACE_UNKNOWN', 'reason': str(error)})
    inventory = {}
    for entry in bundled:
        inventory.setdefault(entry['name'], []).append(entry)
    for name in selection:
        if len(inventory.get(name, [])) != 1:
            issues.append({'code': 'SELECTED_IDENTITY_MISSING_OR_DUPLICATE', 'name': name})
    for owner, dependencies in lock.get('mandatory_dependencies', {}).items():
        for dependency in dependencies:
            if dependency not in inventory or dependency not in selection:
                issues.append({'code': 'MISSING_MANDATORY_DEPENDENCY', 'owner': owner, 'name': dependency})
    if surfaces is None:
        surfaces = {'project': project_root / '.agents/skills', 'project_legacy': project_root / '.codex/skills',
                    'user': Path.home() / '.agents/skills', 'user_codex': Path.home() / '.codex/skills',
                    'enabled_plugins': None, 'managed_or_remote': None}
    # The project's canonical surface is always inspected, even when callers add surfaces.
    surfaces = {'project': project_root / '.agents/skills', **surfaces}
    observed, all_skills, seen_paths = {}, [], set()
    for label, path in surfaces.items():
        try:
            if path is None:
                raise OSError('Surface not enumerable by this portable inspector')
            entries = scan_surface(path)
            observed[label] = {'status': 'observed', 'path': str(path), 'skills': len(entries)}
            for entry in entries:
                key = str(Path(entry['path']).resolve()).casefold()
                if key not in seen_paths:
                    all_skills.append(entry)
                    seen_paths.add(key)
        except (OSError, ValueError) as error:
            observed[label] = {'status': 'unknown', 'path': str(path) if path else None, 'reason': str(error)}
    by_name = {}
    for entry in all_skills:
        by_name.setdefault(entry['name'], []).append(entry)
    duplicates = [{'name': name, 'status': 'identical' if len({x['tree_sha256'] for x in entries}) == 1 else 'conflict', 'implementations': entries}
                  for name, entries in sorted(by_name.items()) if len(entries) > 1]
    differences = []
    for name in selection:
        expected = inventory.get(name, [])
        actual = by_name.get(name, [])
        state = 'missing' if not actual else ('identical' if len(expected) == 1 and all(x['tree_sha256'] == expected[0]['tree_sha256'] for x in actual) else 'customized_conflict')
        differences.append({'name': name, 'status': state, 'action': 'review_only_preserve_existing', 'installed': actual})
    from aitools_hooks import inspect_hooks, proposal, windows_launcher_scripts
    hooks = inspect_hooks(kit_root, project_root)
    hooks['proposal'] = proposal(kit_root)
    hooks['windows_launcher_scripts'] = windows_launcher_scripts(hooks['proposal'])
    return {'schema_version': 1, 'operation': 'preview', 'revision': lock.get('revision'), 'selection': selection,
            'selection_status': 'incomplete' if issues else 'verified_local', 'issues': issues,
            'surfaces': observed, 'duplicate_coverage': 'partial' if any(x['status'] == 'unknown' for x in observed.values()) else 'enumerated_surfaces_only',
            'duplicates': duplicates, 'differences': differences, 'hooks': hooks,
            'remote_calls': False, 'installed_or_activated': False}


def validate_bundle(root):
    """Strict offline integration gate for the distributed vendor lock."""
    root = Path(root)
    lock = read_json(root / 'resources/databricks-aitools/upstream-lock.json')
    issues = validate_lock(root, lock)
    selection = lock.get('selected_skills', [])
    inventory = scan_surface(root / '.agents/skills')
    counts = {}
    for item in inventory:
        counts[item['name']] = counts.get(item['name'], 0) + 1
    for name in selection:
        if counts.get(name) != 1:
            issues.append({'code': 'SELECTED_IDENTITY_MISSING_OR_DUPLICATE', 'name': name})
    for name, dependencies in lock.get('mandatory_dependencies', {}).items():
        for dependency in dependencies:
            if dependency not in selection or counts.get(dependency) != 1:
                issues.append({'code': 'MISSING_MANDATORY_DEPENDENCY', 'owner': name, 'name': dependency})
    if not selection or not lock.get('files'):
        issues.append({'code': 'EMPTY_LOCK'})
    required_hooks = ['databricks-context.py', 'databricks-router.py', 'databricks-auth-helper.py', '_routing_data.json', 'codex-hooks.json']
    locked = {item.get('path') for item in lock.get('files', [])}
    for name in required_hooks:
        path = 'resources/databricks-aitools/hooks/' + name
        if path not in locked:
            issues.append({'code': 'HOOK_RESOURCE_NOT_LOCKED', 'path': path})
    if issues:
        raise ValueError('DATABRICKS_BUNDLE_INVALID: ' + json.dumps(issues, ensure_ascii=False))
    return {'revision': lock['revision'], 'skills': len(selection), 'locked_files': len(locked), 'native_hooks_observed': False}
