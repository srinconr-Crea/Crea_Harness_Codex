"""Empaquetado local reproducible con auditor original y revisiones externas exactas."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / 'artifacts/crea-manual-kit-0.1.5'
def assert_target(target):
    expected = ROOT / 'artifacts/crea-manual-kit-0.1.5'
    if Path(target).resolve() != expected.resolve() or expected.is_symlink() or getattr(expected, 'is_junction', lambda: False)():
        raise ValueError('PACKAGE_TARGET_MUST_BE_NEW_015_STAGING')


sys.path.insert(0, str(KIT / 'scripts/crea'))
from testing.common import read, write, file_hash, digest
from testing.kit_validation import files, validate_kit


def audit(tool, target, identifiers, reviews):
    raw = tool.audit(target, identifiers)
    payloads = {}
    for name, payload in tool.entries(target):
        relative = name.removeprefix(KIT.name + '/')
        payloads[relative] = payload
    accepted, unresolved = [], []
    for finding in raw['findings']:
        row = dict(finding)
        name = row['path'].removeprefix(KIT.name + '/')
        payload = payloads.get(name)
        key = digest({'path': name, 'category': row['category'], 'location': row['location'],
                      'line': row['line'], 'file_sha256': hashlib.sha256(payload).hexdigest() if payload else None})
        if row['category'] != 'external_identifier' and key in reviews:
            accepted.append({'path': name, 'category': row['category'], 'reason': reviews[key]})
        else:
            unresolved.append(row)
    return {'status': 'passed' if not unresolved else 'blocked', 'files_scanned': raw['files_scanned'],
            'identifier_count': raw['identifier_count'], 'raw_finding_count': raw['finding_count'],
            'reviewed_neutral_count': len(accepted), 'unresolved_count': len(unresolved),
            'categories_reviewed': dict(sorted(Counter(x['category'] for x in accepted).items())),
            'reviewed_files': dict(sorted(Counter(x['path'] for x in accepted).items())),
            'unresolved_findings': unresolved,
            'semantic_review': 'Ejemplos sinteticos neutrales, rutas de sistema y fuentes oficiales upstream revisados por contexto; sin identificadores cliente. No se excluyeron archivos de la distribucion.',
            'auditor': 'Herramienta original del paquete de integracion, sin modificar sus patrones.',
            'review_binding': 'Cada aceptacion externa exige categoria/ruta/linea y SHA256 de todo el archivo; identificadores externos nunca se aceptan.'}


def refresh_inventory():
    p = KIT / 'docs/proyecto.json'
    config = read(p)
    observed = {}
    for path in files(KIT):
        if path.name == 'kit-manifest.json':
            continue
        extension = path.suffix or '(sin-extension)'
        observed.setdefault(extension, []).append(path.relative_to(KIT).as_posix())
    config['inventory']['observed_kit_file_types'] = [
        {'extension': ext, 'count': len(names), 'examples': names[:3]} for ext, names in sorted(observed.items())]
    config['inventory']['observed_note'] = 'Inventario de la distribucion 0.1.5 excluyendo manifest y estado local de pruebas; no sustituye inventario del cliente.'
    write(p, config)


def manifest():
    entries = [{'path': p.relative_to(KIT).as_posix(), 'bytes': p.stat().st_size, 'sha256': file_hash(p)}
               for p in files(KIT) if p.name != 'kit-manifest.json']
    write(KIT / 'kit-manifest.json', {'kit': 'crea-manual-kit', 'version': '0.1.5',
                                    'created_on': '2026-10-26', 'source_version': '0.1.4', 'files': entries})


def preservation():
    assert_target(KIT)
    count = 0
    for version in ('0.1.3', '0.1.4'):
        source = KIT.with_name('crea-manual-kit-' + version)
        for row in read(source / 'kit-manifest.json')['files']:
            path = source / row['path']
            if file_hash(path) != row['sha256'] or path.stat().st_size != row['bytes']:
                raise ValueError('SOURCE_DISTRIBUTION_CHANGED: ' + version)
            count += 1
        archive = source.parent / (source.name + '.zip')
        if archive.exists() and file_hash(archive) != archive.with_suffix('.zip.sha256').read_text().split()[0]:
            raise ValueError('PREVIOUS_ZIP_CHANGED: ' + version)
    preserved = 0
    source = KIT.with_name('crea-manual-kit-0.1.4')
    for path in files(source):
        name = path.relative_to(source).as_posix()
        if (name.startswith('.agents/skills/') and not name.startswith('.agents/skills/Crea/')) or name.startswith('docs/licencias/'):
            if file_hash(path) != file_hash(KIT / name):
                raise ValueError('UPSTREAM_OR_LICENSE_CHANGED')
            preserved += 1
    return {'source_manifest_files_verified': count, 'upstream_and_license_files_preserved': preserved,
            'previous_versions_verified': ['0.1.3', '0.1.4']}


def main():
    assert_target(KIT)
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--denylist', type=Path, required=True)
    p.add_argument('--reviews', type=Path, required=True)
    p.add_argument('--evidence', type=Path, required=True)
    p.add_argument('--replace-candidate', action='store_true', help='Reemplazar solo un candidato local 0.1.5 generado previamente')
    args = p.parse_args()
    if (KIT.parent / (KIT.name + '.zip')).exists() and not args.replace_candidate:
        raise ValueError('CANDIDATE_ZIP_EXISTS')
    for prior in ('crea-manual-kit-0.1.3', 'crea-manual-kit-0.1.4'):
        if args.evidence.resolve().is_relative_to((KIT.parent / prior).resolve()):
            raise ValueError('EVIDENCE_MUST_NOT_WRITE_PREVIOUS_DISTRIBUTION')
    for path in (args.denylist, args.reviews, args.evidence):
        if path.resolve().is_relative_to(KIT.resolve()):
            raise ValueError('Audit inputs/evidence must be external to deliverable')
    if any((KIT / name).exists() and any((KIT / name).iterdir()) for name in ('.test-work', '__pycache__', '.venv', '.pytest_cache')):
        raise ValueError('Remove local test state safely before packaging')
    spec = importlib.util.spec_from_file_location('package_neutrality', KIT / 'scripts/crea/audit_neutrality.py')
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    identifiers = read(args.denylist)['identifiers']
    if not identifiers or any(not isinstance(x, str) or not x.strip() for x in identifiers):
        raise ValueError('External identifier list required')
    reviews = read(args.reviews)['reviews']
    preserved = preservation()
    neutral_path = KIT / 'docs/NEUTRALIDAD.json'
    if not neutral_path.exists():
        write(neutral_path, {'status': 'pending'})
    refresh_inventory()
    manifest()
    first = audit(tool, KIT, identifiers, reviews)
    write(args.evidence / 'neutrality-tree.json', first)
    if first['status'] != 'passed':
        raise ValueError('UNRESOLVED_NEUTRALITY_FINDINGS')
    write(neutral_path, first)
    manifest()
    validation = {**validate_kit(KIT, original=True), **preserved}
    final_tree = audit(tool, KIT, identifiers, reviews)
    if final_tree['status'] != 'passed':
        raise ValueError('FINAL_TREE_AUDIT_FAILED')
    output = KIT.parent / (KIT.name + '.zip')
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files(KIT):
            info = zipfile.ZipInfo(KIT.name + '/' + path.relative_to(KIT).as_posix(), (2026, 10, 26, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    archive_report = audit(tool, output, identifiers, reviews)
    if archive_report['status'] != 'passed':
        raise ValueError('ZIP_AUDIT_FAILED')
    with zipfile.ZipFile(output) as z:
        expected = {KIT.name + '/' + path.relative_to(KIT).as_posix(): path for path in files(KIT)}
        if set(z.namelist()) != set(expected) or z.testzip() is not None:
            raise ValueError('ZIP_INVENTORY_FAILED')
        for name, path in expected.items():
            if hashlib.sha256(z.read(name)).hexdigest() != file_hash(path):
                raise ValueError('ZIP_BYTES_MISMATCH')
    sha = file_hash(output)
    output.with_suffix('.zip.sha256').write_text(sha + '  ' + output.name + '\n', encoding='utf-8')
    write(args.evidence / 'neutrality-tree.json', final_tree)
    write(args.evidence / 'neutrality-zip.json', archive_report)
    write(args.evidence / 'package-validation.json', {**validation, 'zip_sha256': sha,
          'zip_bytes': output.stat().st_size, 'zip_entries': len(expected), 'zip_audit': archive_report['status']})
    write(output.with_suffix('.zip.validation.json'), {**validation, 'zip_sha256': sha,
          'neutrality_unresolved': archive_report['unresolved_count'], 'neutrality_reviewed': archive_report['reviewed_neutral_count'],
          'source_preserved': True, 'runtime': 'not_run', 'four_role_pilot': 'not_run'})
    print(json.dumps({'status': 'passed', 'files': len(expected), 'zip_sha256': sha,
                      'neutrality_unresolved': 0, 'neutrality_reviewed': archive_report['reviewed_neutral_count']}))


if __name__ == '__main__':
    main()
