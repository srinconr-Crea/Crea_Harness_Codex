"""Detecta rastros de referencias en carpeta/ZIP; lista sensible siempre externa.

No modifica el árbol auditado. Informe sin valores de origen. El análisis textual
no sustituye revisión semántica ni visual. Excluye solo estado local no distribuible.
"""
import argparse
import json
from pathlib import Path
import re
import zipfile

PATTERNS = {
    'workspace_url': re.compile(r'https?://(?:adb-\d[^\s\"<>)]*|dbc-[a-z0-9][^\s\"<>)]*)', re.I),
    'absolute_windows_path': re.compile(r'\b[A-Z]:[\\/][^\s\"<>)]*', re.I),
    'identity_email': re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', re.I),
    'storage_uri': re.compile(r'\babfss?://[^\s\"<>)]*', re.I),
    'repository_url': re.compile(r'https?://(?:github\.com/[^\s\"<>)]*|dev\.azure\.com/[^\s\"<>)]*)', re.I),
}
EXCLUDED_PARTS = {'.git', '.venv', '__pycache__', '.test-work'}


def scan_text(text, identifiers):
    hits = []
    for line_no, line in enumerate(text.splitlines(), 1):
        folded = line.casefold()
        for index, term in enumerate(identifiers):
            if term.casefold() in folded:
                hits.append({'line':line_no, 'category':'external_identifier','reference_index':index})
        for category, pattern in PATTERNS.items():
            if pattern.search(line):
                hits.append({'line':line_no,'category':category})
    return hits


def entries(target):
    target = Path(target).resolve()
    if target.is_dir():
        for p in sorted(target.rglob('*')):
            if p.is_file() and not any(part in EXCLUDED_PARTS for part in p.relative_to(target).parts):
                if not p.resolve().is_relative_to(target):
                    raise ValueError('External symlink prevents complete audit')
                yield p.relative_to(target).as_posix(), p.read_bytes()
    elif target.is_file() and zipfile.is_zipfile(target):
        with zipfile.ZipFile(target) as z:
            for name in sorted(z.namelist()):
                if not name.endswith('/'):
                    yield name, z.read(name)
    else:
        raise ValueError('Target must be a directory or ZIP')


def audit(target, identifiers):
    files, findings = 0, []
    for name, payload in entries(target):
        files += 1
        text = payload.decode('utf-8',errors='replace')
        report_path = name
        for term in identifiers:
            report_path = re.sub(re.escape(term),'[redacted]',report_path,flags=re.I)
        for category, pattern in PATTERNS.items():
            report_path = pattern.sub('['+category+']',report_path)
        for hit in scan_text(name,identifiers):
            findings.append({'path':report_path,'location':'file_name',**hit})
        for hit in scan_text(text,identifiers):
            findings.append({'path':report_path,'location':'content',**hit})
    return {'status':'passed' if not findings else 'blocked','files_scanned':files,
            'identifier_count':len(identifiers),'finding_count':len(findings),'findings':findings,
            'scope':'textual_and_file_names','semantic_review_required':True}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target',required=True,type=Path)
    p.add_argument('--denylist',required=True,type=Path,help='JSON externo con identifiers: [strings]')
    p.add_argument('--out',type=Path)
    args = p.parse_args()
    try:
        target = args.target.resolve()
        denylist = args.denylist.resolve()
        output = args.out.resolve() if args.out else None
        if target.is_dir() and (denylist.is_relative_to(target) or (output and output.is_relative_to(target))):
            raise ValueError('Denylist and audit report must be outside the audited tree')
        data = json.loads(denylist.read_text(encoding='utf-8-sig'))
        terms = data['identifiers']
        if not isinstance(terms,list) or not terms or any(not isinstance(x,str) or not x.strip() for x in terms):
            raise ValueError('Nonempty external identifier list required')
        report = audit(target,terms)
        text = json.dumps(report,ensure_ascii=False,indent=2)+'\n'
        if args.out:
            args.out.parent.mkdir(parents=True,exist_ok=True)
            args.out.write_text(text,encoding='utf-8')
        else:
            print(text,end='')
        return 0 if report['status']=='passed' else 2
    except (ValueError,KeyError,OSError) as error:
        print(json.dumps({'status':'blocked','error_category':type(error).__name__}))
        return 1


if __name__=='__main__':
    raise SystemExit(main())
