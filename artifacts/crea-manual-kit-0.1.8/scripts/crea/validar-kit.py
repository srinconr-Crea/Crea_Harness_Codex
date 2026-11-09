"""Entrada Python de validación estructural (sin red ni comandos de negocio)."""
import argparse
import json
from pathlib import Path
from testing.kit_validation import validate_kit


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument('--original', action='store_true')
    args = p.parse_args()
    try:
        print(json.dumps(validate_kit(args.root, args.original)))
        return 0
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(json.dumps({'status': 'blocked', 'error': str(exc) if isinstance(exc, ValueError) else type(exc).__name__}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
