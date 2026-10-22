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
