"""CLI local: plan no ejecuta; run ejecuta solo catálogo revisado; gate no repite."""
import argparse
import json
from pathlib import Path
import sys

from testing import git_adapter, workflow
from testing.common import read, safe_path, write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['plan', 'run', 'gate'])
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--policy', default='docs/pruebas/policy.json')
    parser.add_argument('--execution', default='docs/pruebas/execution.json')
    parser.add_argument('--plan', required=True)
    parser.add_argument('--results')
    parser.add_argument('--out')
    parser.add_argument('--git-receipt')
    parser.add_argument('--base')
    parser.add_argument('--criteria', nargs='*', default=[])
    args = parser.parse_args()
    try:
        root = args.repo.resolve()
        from testing.schemas import validate
        project = validate('project', read(safe_path(root, 'docs/proyecto.json')))
        if not project['project']['setup_complete']:
            raise ValueError('PROJECT_SETUP_INCOMPLETE')
        configured = project['validation']['testing']
        if args.policy != configured['policy_path'] or args.execution != configured['execution_path']:
            raise ValueError('CONFIGURED_CATALOG_PATH_REQUIRED')
        policy = safe_path(root, args.policy)
        settings = safe_path(root, args.execution)
        config = validate('execution', read(settings))
        primary = {args.plan, args.results, args.git_receipt}
        for report in config['checks'].values():
            primary.update([report['junit_path'], report['coverage_path']])
            report_parent = Path(report['junit_path']).parent
            for name in config['checks']:
                primary.update((report_parent / (prefix + name + suffix)).as_posix()
                               for prefix, suffix in [('receipt-', '.json'), ('stdout-', '.log'), ('stderr-', '.log')])
        if args.out:
            destination = safe_path(root, args.out)
            for name in primary - {None}:
                source = safe_path(root, name)
                if destination == source or (destination.exists() and source.exists() and destination.samefile(source)):
                    raise ValueError('OUTPUT_COLLIDES_WITH_PRIMARY_EVIDENCE')
        for name, expected in [(args.plan, 'plan.json'), (args.results, 'resultados.json'),
                               (args.out, 'gate.json'), (args.git_receipt, 'git.json')]:
            if name and Path(name).name != expected:
                raise ValueError('ARTIFACT_ROLE_FILENAME_REQUIRED')
        for name in (args.plan, args.results, args.out, args.git_receipt):
            if name and name not in config['outputs']:
                raise ValueError('UNDECLARED_GENERATED_OUTPUT')
            if name:
                lexical = root / name
                for parent in [lexical, *lexical.parents]:
                    if parent == root:
                        break
                    if parent.is_symlink() or getattr(parent, 'is_junction', lambda: False)():
                        raise ValueError('GENERATED_OUTPUT_LINK_NOT_ALLOWED')
        if args.action == 'plan':
            if not args.base:
                raise ValueError('EXPLICIT_GIT_BASE_REQUIRED')
            if safe_path(root, args.plan).exists() or (args.git_receipt and safe_path(root, args.git_receipt).exists()):
                raise ValueError('PLAN_OR_GIT_RECEIPT_EXISTS_USE_NEW_ATTEMPT_PATHS')
            result = workflow.make_plan(root, policy, settings, args.base, args.criteria)
            if args.git_receipt:
                projection = result.get('provenance', {}).get('projection')
                if projection:
                    catalog, _ = workflow.load(policy, settings)
                    observation = git_adapter.content_view(root, args.base, config['outputs'], projection,
                                  [p for check in catalog['checks'] for p in check['inputs']])
                else:
                    observation = git_adapter.collect(root, args.base, config['outputs'])
                write(safe_path(root, args.git_receipt), observation)
            write(safe_path(root, args.plan), result)
        elif args.action == 'run':
            if not args.results or safe_path(root, args.results).exists():
                raise ValueError('NEW_RESULTS_PATH_REQUIRED')
            result = workflow.run(root, policy, settings, read(safe_path(root, args.plan)))
            write(safe_path(root, args.results), result)
        else:
            if not args.results:
                raise ValueError('RESULTS_REQUIRED')
            result = workflow.gate(root, policy, settings, read(safe_path(root, args.plan)), read(safe_path(root, args.results)))
            if args.out:
                write(safe_path(root, args.out), result)
        status = result.get('status', 'blocked' if any(r['status'] != 'passed' for r in result.get('records', [])) else 'passed')
        print(json.dumps({'status': status, 'plan_id': result.get('plan_id'), 'blockers': result.get('blockers', [])}))
        return 2 if status == 'blocked' else 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'blocked', 'error': str(exc) if isinstance(exc, ValueError) else type(exc).__name__}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
