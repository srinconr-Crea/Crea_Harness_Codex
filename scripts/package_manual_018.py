"""Empaquetar exclusivamente el candidato portable 0.1.8; preservar fuentes reales."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / 'artifacts/crea-manual-kit-0.1.8'
EXCLUDED = {'.git', '.venv', '__pycache__', '.test-work', '.pytest_cache'}


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def assert_target(target):
    target = Path(target)
    expected = ROOT / 'artifacts/crea-manual-kit-0.1.8'
    if target.resolve() != expected.resolve() or target.is_symlink() or target.is_junction():
        raise ValueError('PACKAGE_TARGET_MUST_BE_NEW_018_STAGING')


def files(root):
    root = Path(root)
    result = []
    for path in sorted(root.rglob('*')):
        if set(path.relative_to(root).parts) & EXCLUDED:
            continue
        if path.is_symlink() or path.is_junction():
            raise ValueError('PACKAGE_LINK_REJECTED')
        if path.is_file():
            result.append(path)
    return result


def verify_baseline(root, baseline):
    root = Path(root).resolve()
    for row in baseline['files']:
        path = root / row['path']
        if (not path.resolve().is_relative_to(root) or path.is_symlink()
                or not path.is_file() or path.stat().st_size != row['bytes']
                or file_hash(path) != row['sha256']):
            raise ValueError('BASELINE_CHANGED: ' + row['path'])
    return {'source_preserved': True, 'baseline_files_verified': len(baseline['files'])}


def refresh_inventory():
    config = read(KIT / 'docs/proyecto.json')
    observed = {}
    for path in files(KIT):
        if path.name != 'kit-manifest.json':
            observed.setdefault(path.suffix or '(sin-extension)', []).append(path.relative_to(KIT).as_posix())
    config['inventory']['observed_kit_version'] = '0.1.8'
    config['inventory']['observed_kit_file_types'] = [
        {'extension': ext, 'count': len(names), 'examples': names[:3]}
        for ext, names in sorted(observed.items())]
    config['inventory']['observed_note'] = 'Distribucion portable 0.1.8; inventario del kit, no del repositorio cliente.'
    write(KIT / 'docs/proyecto.json', config)


def manifest():
    rows = [{'path': p.relative_to(KIT).as_posix(), 'bytes': p.stat().st_size, 'sha256': file_hash(p)}
            for p in files(KIT) if p != KIT / 'kit-manifest.json']
    write(KIT / 'kit-manifest.json', {'kit': 'crea-manual-kit', 'version': '0.1.8',
          'created_on': '2026-11-09', 'source_version': '0.1.7',
          'source_baseline': 'docs/hu/gestionar-ciclo-vida-pruebas-proyecto/baseline.json', 'files': rows})


def write_archive(kit, output):
    kit, output = Path(kit), Path(output)
    assert_target(kit)
    if output.resolve() != (KIT.parent / (KIT.name + '.zip')).resolve() or output.is_symlink() or output.is_junction():
        raise ValueError('PACKAGE_OUTPUT_MUST_BE_NEW_018_ARCHIVE')
    expected = {kit.name + '/' + p.relative_to(kit).as_posix(): p.read_bytes() for p in files(kit)}
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in expected.items():
            info = zipfile.ZipInfo(name, (2026, 11, 9, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(output) as archive:
        if (len(archive.namelist()) != len(expected) or set(archive.namelist()) != set(expected)
                or archive.testzip() is not None
                or any(archive.read(name) != data for name, data in expected.items())):
            raise ValueError('ZIP_BYTES_MISMATCH')
    return {'zip_entries': len(expected), 'zip_bytes': output.stat().st_size,
            'zip_sha256': file_hash(output), 'tree_zip_equivalent': True}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, default=ROOT / 'docs/hu/gestionar-ciclo-vida-pruebas-proyecto/baseline.json')
    parser.add_argument('--evidence', type=Path, default=ROOT / 'docs/hu/gestionar-ciclo-vida-pruebas-proyecto')
    parser.add_argument('--replace-candidate', action='store_true')
    args = parser.parse_args(argv)
    assert_target(KIT)
    preserved = verify_baseline(ROOT, read(args.baseline))
    evidence = args.evidence.resolve()
    if not evidence.is_relative_to((ROOT / 'docs/hu/gestionar-ciclo-vida-pruebas-proyecto').resolve()) or evidence.is_symlink():
        raise ValueError('EVIDENCE_OUTSIDE_ALLOWED_DIRECTORY')
    evidence.mkdir(parents=True, exist_ok=True)
    output = KIT.parent / (KIT.name + '.zip')
    if output.is_symlink() or output.is_junction():
        raise ValueError('ZIP_LINK_REJECTED')
    if output.exists() and not args.replace_candidate:
        raise ValueError('CANDIDATE_ZIP_EXISTS')
    refresh_inventory()
    manifest()
    # Separate process avoids importing an older kit's cached `testing` package.
    run = subprocess.run([sys.executable, '-B', str(KIT / 'scripts/crea/validar-kit.py'),
                          '--root', str(KIT), '--original'], capture_output=True, text=True, timeout=120)
    if run.returncode:
        raise ValueError('KIT_VALIDATION_FAILED: ' + run.stdout.strip())
    validation = json.loads(run.stdout)
    if output.exists():
        output.unlink()  # Exact newly generated candidate path, never a historical version.
    report = {**validation, **preserved, **write_archive(KIT, output)}
    verify_baseline(ROOT, read(args.baseline))
    report.update({'status': 'passed', 'remote_azure_read': 'not_run', 'native_hooks': 'not_run',
                   'runtime': 'not_run', 'four_role_pilot': 'not_run',
                   'neutrality': 'not_certified_for_updated_upstream'})
    output.with_suffix('.zip.sha256').write_text(report['zip_sha256'] + '  ' + output.name + '\n', encoding='utf-8')
    write(output.with_suffix('.zip.validation.json'), report)
    write(evidence / 'package-validation.json', report)
    print(json.dumps(report))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
