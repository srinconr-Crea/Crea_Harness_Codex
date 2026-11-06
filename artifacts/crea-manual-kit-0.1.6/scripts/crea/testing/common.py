import importlib.util
import json
from pathlib import Path

KIT = Path(__file__).resolve().parents[3]
ASSETS = KIT / '.agents/skills/Crea/crea-pruebas/assets'
spec = importlib.util.spec_from_file_location('crea_contract', ASSETS.parent / 'scripts/contract.py')
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)
digest = contract.digest
safe_path = contract.safe_path
file_hash = contract.file_hash
canonical_bytes = contract.canonical_bytes


def read(path):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError('DUPLICATE_JSON_KEY')
            value[key] = item
        return value
    def invalid_constant(value):
        raise ValueError('NONFINITE_JSON_NUMBER')
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),
                      object_pairs_hook=unique, parse_constant=invalid_constant)


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def error(code):
    raise ValueError(code)


def resolve_reference(root, ref, moves=()):
    path = safe_path(root, ref['path'])
    matches = [row for row in moves if row['from'] == ref['path']]
    if len(matches) > 1:
        raise ValueError('REFERENCE_MOVEMENT_AMBIGUOUS')
    if matches:
        movement = matches[0]
        target = safe_path(root, movement['to'])
        if path.exists() and target.exists():
            raise ValueError('ARCHIVE_SOURCE_AND_DESTINATION_PRESENT')
        path = path if path.exists() else target
        if not path.is_file() or file_hash(path, movement.get('normalization', 'identity')) != movement['sha256']:
            raise ValueError('ARCHIVE_REFERENCE_CONTENT_CHANGED')
    if not path.is_file():
        raise ValueError('REFERENCE_MISSING: ' + ref['path'])
    acceptable = {file_hash(path)}
    if matches:
        acceptable.add(file_hash(path, matches[0].get('normalization', 'identity')))
    if ref.get('sha256') and ref['sha256'] not in acceptable:
        raise ValueError('REFERENCE_CHANGED: ' + ref['path'])
    return path


def render_handoff(handoff, source, source_hash):
    """Una vista reproducible; nunca un segundo registro de estado."""
    identity = handoff['identity']
    lines = [f'<!-- derived_from: {source} sha256: {source_hash} -->',
             f"HU y fase: {identity['hu_id']} / {identity['change']} / {identity['phase']}",
             'Resultado: ' + handoff['result']['status'],
             'Alcance/candidato: ' + handoff['scope']['objective'] + ' / ' + str(handoff['scope']['candidate_digest']),
             'Reglas y evidencia:']
    for rule in handoff['context']['rules']:
        lines.append(f"- {rule['id']}: {rule['path']} ({rule['revision']})")
    refs = list(handoff['evidence']['artifacts']) + list(handoff['scope']['criteria'])
    if handoff['evidence']['tests']:
        refs += list(handoff['evidence']['tests'].values())
    for ref in refs:
        lines.append('- ' + ref['path'])
    lines += ['Bloqueos/pendientes: ' + json.dumps(handoff['pending'], ensure_ascii=False, sort_keys=True),
              'Decisión requerida: ' + json.dumps(handoff['continuation']['decision_required'], ensure_ascii=False, sort_keys=True),
              'Siguiente paso: ' + handoff['continuation']['next_step'],
              'Contrato canónico: ' + source]
    if handoff['evidence']['objects']:
        lines += ['','Inventario de objetos (estados independientes):',
                  json.dumps(handoff['evidence']['objects'], ensure_ascii=False, sort_keys=True, indent=2)]
    if handoff['evidence']['delivery']:
        lines += ['','Entrega:', json.dumps(handoff['evidence']['delivery'], ensure_ascii=False, sort_keys=True, indent=2)]
    return '\n'.join(lines) + '\n'
