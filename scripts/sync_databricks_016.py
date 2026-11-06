"""Reproduce only the reviewed 0.1.6 Databricks payload; never execute upstream."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import urllib.request
import zipfile

REVISION = 'ddf785ffc6afc805e4fc6e48835d8da6f912b402'
REPOSITORY = 'https://github.com/databricks/databricks-agent-skills'
ARCHIVE_ROOT = 'databricks-agent-skills-' + REVISION + '/'
ARCHIVE_URL = 'https://codeload.github.com/databricks/databricks-agent-skills/zip/' + REVISION
ARCHIVE_SHA256 = 'e02fac494135ab8de942581e4fb2e502a799cb56e2d773b127a639e558c756bf'
BASE = 'apps-python core dabs dbsql model-serving unity-catalog docs jobs mlflow-evaluation pipelines python-sdk synthetic-data-gen apps app-design data-discovery'.split()
ADDITIONAL = 'execution-compute lakebase unity-gateway mlflow-tracing ai-functions aibi-dashboards metric-views spark-structured-streaming lakeflow-connect'.split()
DEPENDENCIES = {
    'databricks-jobs': ['databricks-serverless'],
    'databricks-pipelines': ['databricks-serverless'],
    'databricks-execution-compute': ['databricks-sandbox'],
    'databricks-ai-functions': ['databricks-vector-search'],
    'databricks-metric-views': ['databricks-genie-agents'],
}
SELECTED = sorted({'databricks-' + n for n in BASE + ADDITIONAL} | {d for ds in DEPENDENCIES.values() for d in ds})
OPTIONAL = {
    'databricks-ml-training': 'Training and custom model authoring are separate from endpoint operations and UC governance.',
    'databricks-iceberg': 'External engine Iceberg interoperability is a separate workflow.',
    'databricks-zerobus-ingest': 'Push ingestion is an alternative to selected pull connectors.',
    'databricks-setup-local': 'Local environment provisioning is not necessary to consume portable skills.',
    'databricks-ai-runtime': 'GPU training runtime is outside the selected compute workflows.',
    'databricks-serverless-migration': 'Classic migration is separate from compute selection.',
    'databricks-unstructured-pdf-generation': 'PDF generation is a separate workflow.',
}
ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / 'artifacts/crea-manual-kit-0.1.6'
EVIDENCE = ROOT / 'docs/evidence/portable-aitools-devops'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def patch_payload(path, data):
    # No repair required at this revision. Never infer missing references from
    # unnormalized Windows paths exceeding MAX_PATH; normalize first.
    return data, []


def read_archive(path):
    result = {}
    with zipfile.ZipFile(path) as archive:
        for item in archive.infolist():
            if not item.filename.startswith(ARCHIVE_ROOT):
                raise ValueError('archive root is not the pinned revision')
            relative = item.filename[len(ARCHIVE_ROOT):]
            if '..' in PurePosixPath(relative).parts or '\\' in relative or relative.startswith('/'):
                raise ValueError('unsafe archive path')
            if not item.is_dir():
                result[relative] = archive.read(item)
    return result


def verify(kit):
    lock = json.loads((kit / 'resources/databricks-aitools/upstream-lock.json').read_text(encoding='utf-8'))
    errors = []
    names = []
    for name in lock['selected_skills']:
        skill = kit / '.agents/skills' / name / 'SKILL.md'
        if not skill.is_file():
            errors.append('missing skill: ' + name)
            continue
        match = re.search(r'^name:\s*[\"\']?([^\r\n\"\']+)', skill.read_text(encoding='utf-8'), re.M)
        names.append(match.group(1).strip() if match else None)
        if not match or names[-1] != name:
            errors.append('frontmatter identity: ' + name)
    if len(set(names)) != len(names):
        errors.append('duplicate identity')
    for name, dependencies in lock['mandatory_dependencies'].items():
        for dependency in dependencies:
            if dependency not in lock['selected_skills']:
                errors.append('missing dependency: ' + name + ' -> ' + dependency)
    for item in lock['files']:
        path = kit / item['path']
        if not path.is_file() or sha(path.read_bytes()) != item['distributed_sha256']:
            errors.append('hash mismatch: ' + item['path'])
    for name in lock['selected_skills']:
        for path in (kit / '.agents/skills' / name).rglob('*.md'):
            for href in re.findall(r'\]\(([^)\s]+)', path.read_text(encoding='utf-8')):
                target = href.split('#')[0]
                if not target or re.match(r'\w+://|mailto:|\$|<|/', target) or target == 'url':
                    continue
                if any(optional in target for optional in lock['optional_references']):
                    continue
                if not (path.parent / target).resolve().exists():
                    errors.append('missing local reference: ' + path.relative_to(kit).as_posix() + ' -> ' + href)
    return {'revision': lock['revision'], 'skill_count': len(names), 'file_count': len(lock['files']), 'errors': errors}


def sync(archive_path):
    if sha(archive_path.read_bytes()) != ARCHIVE_SHA256:
        raise ValueError('archive does not match the reviewed immutable artifact SHA256')
    files = read_archive(archive_path)
    manifest = json.loads(files['manifest.json'])
    output = {}
    for name in SELECTED:
        entry = manifest['skills'][name]
        prefix = 'plugins/databricks/codex/skills/' + name + '/'
        bundled = {p[len(prefix):] for p in files if p.startswith(prefix)}
        if bundled != set(entry['files']):
            raise ValueError('Codex bundle differs from manifest for ' + name)
        for relative in sorted(bundled):
            output['.agents/skills/' + name + '/' + relative] = prefix + relative
    for relative in ['databricks-router.py', 'databricks-context.py', 'databricks-auth-helper.py', '_routing_data.json', 'codex-hooks.json', 'README.md']:
        output['resources/databricks-aitools/hooks/' + relative] = 'hooks/' + relative
    for relative in ['manifest.json', 'LICENSE', 'NOTICE']:
        output['resources/databricks-aitools/' + relative] = relative
    output['docs/licencias/databricks-agent-skills-LICENSE'] = 'LICENSE'
    output['docs/licencias/databricks-agent-skills-NOTICE'] = 'NOTICE'
    inventory = []
    # All inputs validated before any candidate mutation. Historical roots are constants outside this target.
    for dest, source in sorted(output.items()):
        path = KIT / dest
        path.parent.mkdir(parents=True, exist_ok=True)
        distributed, patches = patch_payload(dest, files[source])
        path.write_bytes(distributed)
        inventory.append({'path': dest, 'upstream_path': source, 'original_sha256': sha(files[source]),
                          'distributed_sha256': sha(distributed), 'source_url': REPOSITORY.replace('github.com', 'raw.githubusercontent.com') + '/' + REVISION + '/' + source, 'patches': patches})
    # Remove stale files only from selected, candidate-local upstream directories.
    wanted = set(output)
    for name in SELECTED:
        target = (KIT / '.agents/skills' / name).resolve()
        target.relative_to(KIT.resolve())
        for path in sorted(target.rglob('*'), reverse=True):
            if path.is_file() and path.relative_to(KIT).as_posix() not in wanted:
                path.unlink()
            elif path.is_dir() and not any(path.iterdir()):
                path.rmdir()
    references = []
    for dest, source in output.items():
        if dest.startswith('.agents/skills/') and dest.endswith('.md'):
            for line_no, line in enumerate(files[source].decode('utf-8').splitlines(), 1):
                for ref in sorted(set(re.findall(r'databricks-[a-z][a-z0-9-]+', line)) & set(manifest['skills'])):
                    owner = dest.split('/')[2]
                    if ref != owner:
                        references.append({'source': dest, 'line': line_no, 'target': ref,
                                           'classification': 'required' if ref in DEPENDENCIES.get(owner, []) else 'included_cross_reference' if ref in SELECTED else 'optional_workflow',
                                           'reason': OPTIONAL.get(ref, 'Selected capability or reviewed dependency.')})
    lock = {'schema_version': 1, 'repository': REPOSITORY, 'revision': REVISION, 'reviewed_on': '2026-11-06',
            'archive_url': ARCHIVE_URL, 'archive_sha256': sha(archive_path.read_bytes()), 'license': 'Apache-2.0',
            'selected_skills': SELECTED, 'mandatory_dependencies': DEPENDENCIES, 'optional_references': OPTIONAL,
            'references': references, 'files': inventory,
            'selection_reasons': {n: 'Existing skill updated' if n[11:] in BASE else 'Design 2 selected capability' if n[11:] in ADDITIONAL else 'Reviewed workflow dependency' for n in SELECTED},
            'apps_patch': {'applied': False, 'reason': 'Upstream proto-first.md already links proto-contracts.md; prior local repair is obsolete.'},
            'hooks_state': {'included': True, 'configured': False, 'authorized': False, 'observed': False}}
    (KIT / 'resources/databricks-aitools/upstream-lock.json').write_text(json.dumps(lock, indent=2) + '\n', encoding='utf-8')
    provenance_path = KIT / 'docs/skills-procedencia.json'
    provenance = json.loads(provenance_path.read_text(encoding='utf-8'))
    preserved = [s for s in provenance['skills'] if not s['name'].startswith('databricks-')]
    provenance['skills'] = preserved + [{'name': n, 'origin': REPOSITORY, 'revision': REVISION, 'upstream_path': 'plugins/databricks/codex/skills/' + n,
        'modified': any(i['patches'] for i in inventory if i['path'].startswith('.agents/skills/' + n + '/')),
        'patches': [p for i in inventory if i['path'].startswith('.agents/skills/' + n + '/') for p in i['patches']],
        'license': 'Apache-2.0', 'reason': lock['selection_reasons'][n],
        'file_inventory': 'resources/databricks-aitools/upstream-lock.json'} for n in SELECTED]
    provenance.update({'reviewed_on': '2026-11-06', 'databricks_lock': 'resources/databricks-aitools/upstream-lock.json',
                       'note': 'Databricks Codex bundle pinned to one revision; non-Databricks provenance preserved. Per-file original/distributed hashes and optional workflow classifications in lock. No Apps patch needed.'})
    provenance_path.write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return verify(KIT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--download', action='store_true')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    if args.verify_only:
        result = verify(KIT)
    else:
        archive = args.archive or EVIDENCE / 'databricks-upstream.zip'
        if args.download:
            if archive.exists():
                raise ValueError('download destination exists; provide a new --archive')
            with urllib.request.urlopen(ARCHIVE_URL, timeout=90) as response:
                archive.write_bytes(response.read())
        result = sync(archive)
    print(json.dumps(result, indent=2))
    return bool(result['errors'])


if __name__ == '__main__':
    raise SystemExit(main())
