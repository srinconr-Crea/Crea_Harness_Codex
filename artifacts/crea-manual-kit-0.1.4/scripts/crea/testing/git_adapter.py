"""Inventario Git NUL: base/HEAD/index/worktree/untracked y conflictos reales."""
import hashlib
from pathlib import Path
import re
import subprocess

from .common import digest, safe_path


def git(root, *args):
    p = subprocess.run(['git', '-c', 'core.quotepath=false', *args], cwd=root,
                       capture_output=True, timeout=30)
    if p.returncode:
        raise ValueError('GIT_OPERATION_FAILED: ' + args[0])
    return p.stdout


def parse_diff(raw):
    tokens = raw.decode('utf-8', errors='strict').split('\0')
    rows, i = [], 0
    while i < len(tokens) and tokens[i]:
        status = tokens[i][0]
        i += 1
        if status in ('R', 'C'):
            old, name = tokens[i:i+2]
            i += 2
            status = 'R'
        else:
            old, name = None, tokens[i]
            i += 1
        rows.append({'status': status, 'path': name, 'old_path': old})
    return rows


def validate_outputs(outputs):
    if len(set(outputs)) != len(outputs):
        raise ValueError('DUPLICATE_OUTPUT')
    for name in outputs:
        # Exact paths only. No glob, arbitrary documentation, fixtures or source.
        if not re.fullmatch(r'docs/hu/[a-zA-Z0-9_-]+/pruebas/(?:attempt-[a-zA-Z0-9_-]+/)?(?:plan|changes|git|resultados|gate|receipt-[a-zA-Z0-9_-]+|coverage-[a-zA-Z0-9_-]+)\.json|docs/hu/[a-zA-Z0-9_-]+/pruebas/(?:attempt-[a-zA-Z0-9_-]+/)?(?:junit-[a-zA-Z0-9_-]+\.xml|(?:stdout|stderr)-[a-zA-Z0-9_-]+\.log|resumen\.md)', name):
            raise ValueError('INVALID_GENERATED_OUTPUT')


def collect(root, base, outputs):
    root = Path(root).resolve()
    if Path(git(root, 'rev-parse', '--show-toplevel').decode().strip()).resolve() != root:
        raise ValueError('NOT_REPOSITORY_ROOT')
    validate_outputs(outputs)
    base_sha = git(root, 'rev-parse', '--verify', base + '^{commit}').decode().strip()
    head_sha = git(root, 'rev-parse', 'HEAD').decode().strip()
    git(root, 'merge-base', '--is-ancestor', base_sha, head_sha)
    layers = {
        'head': parse_diff(git(root, 'diff', '--no-ext-diff', '--name-status', '-z', '-M', base_sha, 'HEAD', '--')),
        'staged': parse_diff(git(root, 'diff', '--no-ext-diff', '--cached', '--name-status', '-z', '-M', '--')),
        'unstaged': parse_diff(git(root, 'diff', '--no-ext-diff', '--name-status', '-z', '-M', '--')),
        'untracked': [{'status': 'A', 'path': x, 'old_path': None} for x in
                      git(root, 'ls-files', '--others', '--exclude-standard', '-z').decode('utf-8').split('\0') if x],
        'conflicts': [{'status': 'U', 'path': x, 'old_path': None} for x in
                      git(root, 'diff', '--name-only', '--diff-filter=U', '-z', '--').decode('utf-8').split('\0') if x]
    }
    excluded, snapshot, all_rows = [], {}, {}
    filtered = {}
    for layer, rows in layers.items():
        filtered[layer] = []
        for row in rows:
            names = [n for n in (row['path'], row['old_path']) if n]
            for name in names:
                p = safe_path(root, name)
                if p.is_symlink() or (p.exists() and not p.is_file()):
                    raise ValueError('UNSUPPORTED_GIT_INPUT_TYPE')
                if name not in outputs:
                    snapshot[name] = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
            if all(n in outputs for n in names):
                p = safe_path(root, row['path'])
                excluded.append({'layer': layer, 'path': row['path'],
                                 'sha256': hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None,
                                 'reason': 'declared_generated_test_output'})
                continue
            filtered[layer].append(row)
            all_rows[(row['path'], row['old_path'] or '', row['status'])] = row
    index = []
    for token in git(root, 'ls-files', '--stage', '-z').decode('utf-8').split('\0'):
        if not token:
            continue
        metadata, name = token.split('\t', 1)
        if name not in outputs:
            index.append([name, metadata])
    receipt = {'schema_version': '1.0', 'base_sha': base_sha, 'head_sha': head_sha,
               'layers': layers, 'changes': [all_rows[k] for k in sorted(all_rows)],
               'excluded': excluded, 'outputs': sorted(outputs)}
    receipt['input_digest'] = digest({'base': base_sha, 'head': head_sha, 'layers': filtered,
                                      'index': sorted(index), 'worktree': snapshot,
                                      'outputs': sorted(outputs)})
    return receipt
