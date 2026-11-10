"""Preview de composición: lista archivos de copia; no instala ni cambia el cliente."""
import argparse
from fnmatch import fnmatchcase
import json
import os
from pathlib import Path

from team_common import read, safe_path

GROUPS=('client_required','distribution_only','local_only')
LOCAL_STATE={'.git','.venv','venv','node_modules','__pycache__','.test-work','.pytest_cache'}


def configuration(root):
    value=read(safe_path(root,'kit-composition.json'))
    if (not isinstance(value,dict) or value.get('schema_version')!='1.0'
        or set(value)-{'schema_version',*GROUPS,'reasons'}):
        raise ValueError('COMPOSITION_CONTRACT_INVALID')
    for group in GROUPS:
        if not isinstance(value.get(group),list) or any(not isinstance(p,str) or not p or p.startswith('/')
            or '\\' in p or ':' in p or '..' in p.split('/') for p in value[group]):
            raise ValueError('COMPOSITION_PATTERN_INVALID')
    return value


def classify(value,name):
    matches=[group for group in GROUPS if any(fnmatchcase(name,p) for p in value[group])]
    if len(matches)!=1:raise ValueError('COMPOSITION_UNCLASSIFIED_OR_AMBIGUOUS: '+name)
    return matches[0]


def select(root):
    root=Path(root).resolve();value=configuration(root);result={group:[] for group in GROUPS}
    for folder,dirs,files in os.walk(root,followlinks=False):
        for name in list(dirs):
            path=Path(folder)/name
            if name in LOCAL_STATE:
                dirs.remove(name);continue
            relative=path.relative_to(root).as_posix()+'/'
            if any(fnmatchcase(relative,p) for p in value['local_only']):
                dirs.remove(name);continue
            if path.is_symlink() or path.is_junction():raise ValueError('COMPOSITION_LINK_NOT_ALLOWED')
        for name in files:
            path=Path(folder)/name;relative=path.relative_to(root).as_posix()
            group=classify(value,relative)
            if group!='local_only':safe_path(root,relative)
            result[group].append(relative)
    return {group:sorted(paths) for group,paths in result.items()}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args()
    try:print(json.dumps(select(args.root),ensure_ascii=False));return 0
    except (ValueError,OSError) as exc:
        print(json.dumps({'status':'blocked','error':str(exc) if isinstance(exc,ValueError) else type(exc).__name__}));return 4


if __name__=='__main__':raise SystemExit(main())
