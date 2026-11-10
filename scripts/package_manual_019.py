"""Empaquetar candidato 0.1.9 sin mutar la fuente ni distribuciones históricas."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
KIT=ROOT/'artifacts/crea-manual-kit-0.1.9'
EVIDENCE=ROOT/'docs/hu/habilitar-trabajo-multidesarrollador-kit'


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def file_hash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def assert_target(target):
    target=Path(target)
    if target.resolve()!=KIT.resolve() or target.is_symlink() or target.is_junction():
        raise ValueError('PACKAGE_TARGET_MUST_BE_NEW_019_STAGING')


def verify_baseline(root,baseline):
    root=Path(root).resolve()
    for row in baseline['files']:
        path=root/row['path']
        if (not path.resolve().is_relative_to(root) or path.is_symlink() or path.is_junction()
            or not path.is_file() or path.stat().st_size!=row['bytes'] or file_hash(path)!=row['sha256']):
            raise ValueError('HISTORICAL_BASELINE_CHANGED: '+row['path'])
    return {'source_preserved':True,'baseline_files_verified':len(baseline['files'])}


def composition(root):
    # Standalone subprocess prevents cached testing/common from an older kit being used.
    result=subprocess.run([sys.executable,'-B',str(root/'scripts/crea/composicion.py'),'--root',str(root)],
                          capture_output=True,text=True,timeout=60)
    if result.returncode:raise ValueError('COMPOSITION_INVALID: '+result.stdout.strip())
    return json.loads(result.stdout)


def files(root):
    selected=composition(root)
    return [root/name for name in sorted(selected['client_required']+selected['distribution_only'])]


def prepare_manifest():
    assert_target(KIT)
    config=read(KIT/'docs/proyecto.json');observed={}
    for path in files(KIT):
        if path.name!='kit-manifest.json':observed.setdefault(path.suffix or '(sin-extension)',[]).append(path.relative_to(KIT).as_posix())
    config['inventory'].update({'observed_kit_version':'0.1.9','observed_on':'2026-11-10',
        'observed_note':'Distribución portable 0.1.9; inventario del paquete, no arquitectura cliente.',
        'observed_kit_file_types':[{'extension':ext,'count':len(names),'examples':names[:3]} for ext,names in sorted(observed.items())]})
    write(KIT/'docs/proyecto.json',config)
    rows=[{'path':p.relative_to(KIT).as_posix(),'bytes':p.stat().st_size,'sha256':file_hash(p)}
          for p in files(KIT) if p.name!='kit-manifest.json']
    write(KIT/'kit-manifest.json',{'kit':'crea-manual-kit','version':'0.1.9','created_on':'2026-11-10',
        'source_version':'0.1.8','source_baseline':'docs/hu/habilitar-trabajo-multidesarrollador-kit/baseline.json','files':rows})
    return rows


def write_archive(output,replace=False):
    assert_target(KIT);output=Path(output)
    if output.resolve()!=(KIT.parent/(KIT.name+'.zip')).resolve() or output.is_symlink() or output.is_junction():
        raise ValueError('PACKAGE_OUTPUT_MUST_BE_NEW_019_ARCHIVE')
    if output.exists() and not replace:raise ValueError('CANDIDATE_ZIP_EXISTS')
    entries={KIT.name+'/'+p.relative_to(KIT).as_posix():p.read_bytes() for p in files(KIT)}
    mode='w' if replace else 'x'
    with zipfile.ZipFile(output,mode,compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,data in entries.items():
            info=zipfile.ZipInfo(name,(2026,11,10,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            archive.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None or set(archive.namelist())!=set(entries) or len(archive.namelist())!=len(entries):raise ValueError('ZIP_FILESET_MISMATCH')
        if any(archive.read(name)!=data for name,data in entries.items()):raise ValueError('ZIP_BYTES_MISMATCH')
    return {'zip_entries':len(entries),'zip_sha256':file_hash(output),'tree_zip_equivalent':True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest-only',action='store_true');parser.add_argument('--replace-candidate',action='store_true')
    args=parser.parse_args();assert_target(KIT)
    baseline=read(EVIDENCE/'baseline.json');preserved=verify_baseline(ROOT,baseline)
    rows=prepare_manifest()
    checked=subprocess.run([sys.executable,'-B',str(KIT/'scripts/crea/validar-kit.py'),'--root',str(KIT),'--original'],capture_output=True,text=True,timeout=120)
    if checked.returncode:raise ValueError('KIT_VALIDATION_FAILED: '+checked.stdout+checked.stderr)
    value={**json.loads(checked.stdout),**preserved,'manifest_files':len(rows)}
    if not args.manifest_only:
        output=KIT.parent/(KIT.name+'.zip');value.update(write_archive(output,args.replace_candidate))
        output.with_suffix('.zip.sha256').write_text(value['zip_sha256']+'  '+output.name+'\n',encoding='utf-8')
        value.update({'runtime':'not_run','remote_azure_read':'not_run','native_hooks':'not_run','four_role_pilot':'not_run'})
        write(output.with_suffix('.zip.validation.json'),value)
    verify_baseline(ROOT,baseline)
    print(json.dumps(value,ensure_ascii=False));return 0


if __name__=='__main__':raise SystemExit(main())
