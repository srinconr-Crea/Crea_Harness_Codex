#!/usr/bin/env python3
"""Portable AI Tools inspection and fail-open advisory hook launcher."""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

from aitools_inventory import export_new, preview
from aitools_hooks import EVENTS, run_advisory


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    inspect = sub.add_parser('preview', help='Offline inspection; optional exclusive new report inside project')
    inspect.add_argument('--config', required=True)
    inspect.add_argument('--out')
    hook = sub.add_parser('hook', help='Advisory native launcher; does not activate or authorize hooks')
    hook.add_argument('--event', choices=EVENTS, required=True)
    args = parser.parse_args(argv)
    if args.command == 'hook':
        output, _ = run_advisory(args.event, sys.stdin.read(), Path(__file__).resolve().parents[2])
        print(json.dumps(output, ensure_ascii=False))
        return 0
    try:
        report = preview(args.config)
        if args.out:
            export_new(report, args.out, Path(args.config).resolve().parent.parent)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report['selection_status'] == 'verified_local' else 1
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'status': 'invalid_input', 'error': str(error)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
