"""Inventario Git NUL: base/HEAD/index/worktree/untracked y conflictos reales."""
import hashlib
from pathlib import Path
import re
import subprocess

from .common import digest, safe_path, file_hash, read, resolve_reference, canonical_bytes

PHASE_PATTERN = r'(planificacion|implementacion|pruebas|revision|cierre|entrega)'


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


def tree(root, ref):
    """Tree identity without checkout, filters, or remote access."""
    result = {}
    for token in git(root, 'ls-tree', '-rz', ref).decode('utf-8').split('\0'):
        if token:
            metadata, name = token.split('\t', 1)
            mode, kind, oid = metadata.split()
            if kind != 'blob' or mode == '120000':
                raise ValueError('UNSUPPORTED_GIT_INPUT_TYPE')
            result[name] = {'mode': mode, 'oid': oid}
    return result


def observe(root):
    root = Path(root).resolve()
    if Path(git(root, 'rev-parse', '--show-toplevel').decode().strip()).resolve() != root:
        raise ValueError('NOT_REPOSITORY_ROOT')
    index = {}
    for token in git(root, 'ls-files', '--stage', '-z').decode('utf-8').split('\0'):
        if token:
            metadata, name = token.split('\t', 1)
            index.setdefault(name, []).append(metadata)
    names = set(index)
    names.update(n for n in git(root, 'ls-files', '--others', '--exclude-standard', '-z').decode('utf-8').split('\0') if n)
    algorithm = git(root, 'rev-parse', '--show-object-format').decode().strip()
    if algorithm not in ('sha1', 'sha256'):
        raise ValueError('GIT_OBJECT_FORMAT_UNSUPPORTED')
    files = {}
    for name in sorted(names):
        path = safe_path(root, name)
        if not path.exists():
            continue
        if not path.is_file():
            raise ValueError('UNSUPPORTED_GIT_INPUT_TYPE')
        payload = path.read_bytes()
        mode = index[name][0].split()[0] if name in index else '100644'
        if mode == '120000':
            raise ValueError('UNSUPPORTED_GIT_INPUT_TYPE')
        files[name] = {'sha256': hashlib.sha256(payload).hexdigest(), 'mode': mode,
                       'oid': hashlib.new(algorithm, b'blob ' + str(len(payload)).encode() + b'\0' + payload).hexdigest()}
    return {'kind': 'snapshot', 'schema_version': '1.0',
            'head_sha': git(root, 'rev-parse', 'HEAD').decode().strip(),
            'branch': git(root, 'branch', '--show-current').decode().strip(),
            'files': files, 'index': index}


def scope_changes(entry, current):
    if entry.get('kind') != 'snapshot' or current.get('kind') != 'snapshot':
        raise ValueError('SCOPE_BASELINE_REQUIRED')
    names = set(entry['files']) | set(current['files']) | set(entry['index']) | set(current['index'])
    changes = [n for n in names if entry['files'].get(n) != current['files'].get(n)
               or entry['index'].get(n) != current['index'].get(n)]
    if entry['head_sha'] != current['head_sha']:
        changes.append('.git/HEAD')
    if entry['branch'] != current['branch']:
        changes.append('.git/branch')
    if entry['index'] != current['index']:
        changes.append('.git/index')
    return sorted(changes)


def verify_index(root, paths):
    from fnmatch import fnmatchcase
    observation = observe(root)
    staged = parse_diff(git(root, 'diff', '--no-ext-diff', '--cached', '--name-status', '-z', '-M', '--'))
    for row in staged:
        for name in (row['path'], row['old_path']):
            if name and not any(fnmatchcase(name, pattern) for pattern in paths):
                raise ValueError('STAGED_OUTSIDE_APPROVED_SCOPE: ' + name)
    for name in paths:
        safe_path(root, name)
        current = observation['files'].get(name)
        staged = observation['index'].get(name)
        if current is None and staged is None:
            continue
        if not current or not staged or len(staged) != 1:
            raise ValueError('INDEX_DIFFERS_FROM_TESTED_CONTENT: ' + name)
        mode, oid, stage = staged[0].split()
        if stage != '0' or (mode, oid) != (current['mode'], current['oid']):
            raise ValueError('INDEX_DIFFERS_FROM_TESTED_CONTENT: ' + name)
    return observation


def verify_commit(root, base, ref, view, allowed_paths):
    from fnmatch import fnmatchcase
    actual = tree(root, ref)
    omitted = {row['path'] for row in view['excluded']}
    expected = view['observation']['files']
    for name in set(actual) | set(expected):
        if name in omitted:
            if name in actual and (name not in expected or any(actual[name][k] != expected[name][k] for k in ('oid', 'mode'))):
                raise ValueError('COMMIT_DIFFERS_FROM_REVIEWED_METADATA: ' + name)
            continue
        if name not in actual or name not in expected or any(actual[name][k] != expected[name][k] for k in ('oid', 'mode')):
            raise ValueError('COMMIT_DIFFERS_FROM_TESTED_CONTENT: ' + name)
    commits = git(root, 'rev-list', base + '..' + ref).decode().splitlines()
    for commit in commits:
        names = git(root, 'diff-tree', '--no-commit-id', '--name-only', '-r', '-z', commit).decode('utf-8').split('\0')
        for name in (n for n in names if n):
            if not any(fnmatchcase(name, pattern) for pattern in allowed_paths):
                raise ValueError('COMMIT_OUTSIDE_APPROVED_SCOPE: ' + name)
    return True


def handoff_context(handoff):
    scope, context = handoff['scope'], handoff['context']
    return {'objective': scope['objective'], 'criteria': scope['criteria'],
            'approved_paths': scope['approved_paths'], 'layers': context['layers'],
            'capabilities': context['capabilities'], 'rules': context['rules'],
            'functional_decisions': context['functional_decisions'], 'risk': context['risk'],
            'moves': scope['moves'], 'sync': scope['sync'], 'git_inputs': scope['git_inputs']}


def validate_predecessor(root, h, name):
    previous = h['previous_handoff']
    identity = h['identity']
    if identity['attempt'] > 1:
        expected = f"docs/hu/{identity['change']}/handoffs/{identity['phase']}-{identity['attempt']-1}.json"
        if not previous or previous.get('path') != expected or not previous.get('sha256'):
            raise ValueError('HASH_BOUND_PREDECESSOR_REQUIRED')
    if previous:
        if previous['path'] == name or not previous.get('sha256'):
            raise ValueError('INVALID_PREDECESSOR_REFERENCE')
        source = resolve_reference(root, previous, h['scope']['moves'])
        prior = read(source)['identity']
        if prior['change'] != identity['change'] or (identity['attempt'] > 1 and
                (prior['phase'] != identity['phase'] or prior['attempt'] != identity['attempt']-1)):
            raise ValueError('PREDECESSOR_IDENTITY_MISMATCH')


def managed(root, name, projection):
    """Validate generated data; path grammar alone never grants exclusion."""
    prefix = 'docs/hu/' + projection['change'] + '/'
    if not name.startswith(prefix):
        return False
    from .common import render_handoff
    from .schemas import validate_schema
    suffix = name[len(prefix):]
    path = safe_path(root, name)
    if not path.is_file():
        return False
    if re.fullmatch(r'handoffs/(planificacion|implementacion|pruebas|revision|cierre|entrega)-[1-9][0-9]*\.json', suffix):
        h = read(path)
        from .common import KIT
        validate_schema(read(KIT / 'docs/plantillas/handoff.schema.json'), h)
        expected = f"handoffs/{h['identity']['phase']}-{h['identity']['attempt']}.json"
        if h['identity']['change'] != projection['change'] or suffix != expected:
            raise ValueError('HANDOFF_IDENTITY_MISMATCH')
        if name in projection.get('history', {}) and projection['history'][name] != file_hash(path):
            raise ValueError('HISTORIC_HANDOFF_CHANGED')
        validate_predecessor(root, h, name)
        if handoff_context(h) != projection['context']:
            if projection.get('history', {}).get(name) != file_hash(path):
                raise ValueError('HANDOFF_CONTEXT_CHANGED')
        return True
    if re.fullmatch(r'handoffs/(planificacion|implementacion|pruebas|revision|cierre|entrega)-[1-9][0-9]*-(entrada|salida|informe)\.json', suffix):
        data = read(path)
        from .common import KIT
        schema = read(KIT / 'docs/plantillas/handoff.schema.json')
        definition = 'snapshot' if not suffix.endswith('-informe.json') else 'report'
        validate_schema({'$schema': schema['$schema'], '$defs': schema['$defs'], '$ref': '#/$defs/' + definition}, data)
        return True
    if suffix in ('evidencia.md', 'pr.md', 'resumen.md'):
        text = path.read_text(encoding='utf-8-sig')
        match = re.match(r'<!-- derived_from: ([^ ]+) sha256: ([a-f0-9]{64}) -->\n', text)
        if not match or not match[1].startswith(prefix + 'handoffs/') or match[1] == name:
            return False
        source = safe_path(root, match[1])
        if file_hash(source) != match[2] or not managed(root, match[1], projection):
            raise ValueError('DERIVED_SOURCE_CHANGED')
        return text == render_handoff(read(source), match[1], match[2])
    if suffix in ('pr-title.txt', 'pr-body.md'):
        sources = []
        for source in path.parent.joinpath('handoffs').glob('*.json'):
            if re.fullmatch(PHASE_PATTERN + r'-[1-9][0-9]*\.json', source.name):
                h = read(source)
                if handoff_context(h) == projection['context'] and h['evidence']['delivery']:
                    sources.append((h['identity']['created_at'], h['identity']['attempt'], source, h))
        if not sources:
            return False
        _, _, source, h = max(sources, key=lambda row: (row[0], row[1], row[2].name))
        if not managed(root, source.relative_to(root).as_posix(), projection):
            return False
        field = 'title' if suffix == 'pr-title.txt' else 'body'
        normalize = lambda value: value.replace('\r\n', '\n').removesuffix('\n')
        return normalize(path.read_text(encoding='utf-8-sig')) == normalize(h['evidence']['delivery'][field])
    return False


def content_view(root, base, outputs, projection, check_inputs=()):
    root = Path(root).resolve()
    if projection.get('version') != 'content-v2':
        raise ValueError('PROJECTION_VERSION_UNSUPPORTED')
    validate_outputs(outputs)
    from fnmatch import fnmatchcase
    observation = observe(root)
    base_sha = git(root, 'rev-parse', '--verify', base + '^{commit}').decode().strip()
    git(root, 'merge-base', '--is-ancestor', base_sha, observation['head_sha'])
    baseline = tree(root, base_sha)
    files = dict(observation['files'])
    excluded = []
    for name in sorted(set(files) | set(baseline)):
        generated = name in outputs
        if not generated and name in files:
            generated = managed(root, name, projection)
        if generated:
            if any(fnmatchcase(name, pattern) for pattern in check_inputs):
                raise ValueError('GENERATED_OUTPUT_IS_A_CHECK_INPUT')
            excluded.append({'path': name, 'sha256': files.get(name, {}).get('sha256'),
                             'generator': 'plan/run outputs' if name in outputs else 'Crea handoff schema/render 1.0',
                             'canonical_context_digest': digest(projection['context']),
                             'reason': 'declared_test_output' if name in outputs else 'validated_derived_metadata'})
            files.pop(name, None)
            baseline.pop(name, None)
    for movement in projection['moves']:
        old, new = movement['from'], movement['to']
        safe_path(root, old)
        safe_path(root, new)
        if old in files and new in files:
            raise ValueError('ARCHIVE_SOURCE_AND_DESTINATION_PRESENT')
        present = new if new in files else old
        normalization = movement.get('normalization', 'identity')
        if normalization != 'identity' and any(fnmatchcase(name, pattern) for name in (old, new) for pattern in check_inputs):
            raise ValueError('TASK_PROGRESS_IS_A_FUNCTIONAL_CHECK_INPUT')
        actual_path = safe_path(root, present)
        if present not in files or file_hash(actual_path, normalization) != movement['sha256']:
            raise ValueError('ARCHIVE_CONTENT_CHANGED')
        files[old] = files.pop(present)
        if normalization != 'identity':
            payload = canonical_bytes(actual_path, normalization)
            algorithm = git(root, 'rev-parse', '--show-object-format').decode().strip()
            files[old] = {**files[old], 'sha256': hashlib.sha256(payload).hexdigest(),
                          'oid': hashlib.new(algorithm, b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()}
        if new in baseline:
            baseline[old] = baseline.pop(new)
    for sync in projection['sync']:
        name = sync['path']
        safe_path(root, name)
        actual = files.get(name, {}).get('sha256')
        if any(fnmatchcase(name, pattern) for pattern in check_inputs):
            raise ValueError('SYNC_TARGET_IS_A_CHECK_INPUT')
        if actual not in (sync['before_sha256'], sync['after_sha256']):
            raise ValueError('SYNC_CONTENT_CHANGED')
        # The full observed tree still includes this exact authorized transform.
        if sync['before_sha256'] is None:
            files.pop(name, None)
            baseline.pop(name, None)
        else:
            files[name] = dict(sync['before_entry'])
    changes = []
    for name in sorted(set(files) | set(baseline)):
        prior, current = baseline.get(name), files.get(name)
        status = 'A' if prior is None else 'D' if current is None else 'M'
        if len(observation['index'].get(name, [])) > 1:
            changes.append({'path': name, 'old_path': None, 'status': 'U'})
            continue
        if prior and current and all(prior[k] == current[k] for k in ('mode', 'oid')):
            continue
        changes.append({'path': name, 'old_path': None, 'status': status})
    git_inputs = {}
    for check, inputs in projection['git_inputs'].items():
        git_inputs[check] = {}
        for field in inputs:
            key = {'HEAD': 'head_sha', 'branch': 'branch', 'index': 'index'}.get(field)
            if key is None:
                raise ValueError('GIT_INPUT_NOT_SUPPORTED: ' + check)
            git_inputs[check][field] = observation[key]
    identity = {'version': 'content-v2', 'base': base_sha, 'files': files,
                'policy': projection, 'git_inputs': git_inputs}
    return {'base_sha': base_sha, 'changes': changes, 'input_digest': digest(identity),
            'observation': observation, 'excluded': excluded, 'manifest': files}
