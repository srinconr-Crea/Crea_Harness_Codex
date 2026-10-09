"""Bounded onboarding execution and conservative, explicit recovery."""
from contextlib import ExitStack
from importlib.resources import files
import json
from pathlib import Path
import uuid

from harness_core.configuration import ConfigError, digest, load_document, safe_path, validate_configuration
from harness_core.contracts import Binding, Policy, identifier
from harness_core.onboarding_plan import (Journal, JournalOperation, load_json, load_plan,
    absolute_path, authorize, canonical, destination_path, separate, sha)
from .diagnostics import Check, checkout, doctor, probe, report
from .execution_state import CheckoutLock, ensure_state, persist
from .onboarding import preview
from .resources import kit
from .windows_fs import PinnedTree


def content_map(plan):
    resources, manifest = kit()
    if manifest != plan.resource_manifest_sha256:
        raise ConfigError('invalid_plan')
    resources[f'{plan.descriptor.openspec_root}/config.yaml'] = resources.pop('openspec/config.yaml')
    resources['AGENTS.md'] = files('harness_local').joinpath('templates/AGENTS.md').read_text(encoding='utf-8')
    resources['.harness/client.yaml'] = json.dumps(plan.descriptor.model_dump(), ensure_ascii=False, sort_keys=True, indent=2) + '\n'
    return resources


def selected(plan, target, policy_path):
    target, origin = checkout(target)
    policy_path = absolute_path(str(safe_path(policy_path)))
    if target != absolute_path(plan.target_path) or policy_path != absolute_path(plan.policy_path):
        raise ConfigError('plan_identity_mismatch')
    if digest(policy_path) != plan.policy_sha256 or origin != plan.origin:
        raise ConfigError('stale_plan')
    config = validate_configuration(target, policy_path, plan.binding_path, origin,
                                    descriptor=plan.descriptor, proposed_binding=plan.binding)
    if plan.input_hashes.get('policy') != plan.policy_sha256:
        raise ConfigError('invalid_plan')
    contents = content_map(plan)
    permitted_hashes = {'policy', 'binding', 'descriptor', 'AGENTS.md', '.codex/config.toml', *contents}
    if not set(plan.input_hashes) <= permitted_hashes or 'binding' not in plan.input_hashes:
        raise ConfigError('invalid_plan')
    binding_content = json.dumps(plan.binding.model_dump(), ensure_ascii=False, sort_keys=True, indent=2) + '\n'
    expected_absent = []
    for op in plan.operations:
        expected = contents.get(op.path) if op.scope == 'target' else binding_content
        if (expected != op.content or (op.scope == 'binding' and
            (plan.binding_mode != 'proposed' or op.path != plan.binding_path))):
            raise ConfigError('invalid_plan')
        if op.scope == 'target':
            expected_absent.append(op.path)
    if sorted(expected_absent) != plan.absent_paths or (plan.binding_mode == 'proposed' and
            (sum(o.scope == 'binding' for o in plan.operations) != 1 or sha(binding_content.encode()) != plan.input_hashes['binding'])):
        raise ConfigError('invalid_plan')
    if not plan.applicable or authorize(plan.operations, config['policy']):
        raise ConfigError('plan_not_applicable')
    # Existing bindings are explicit preconditions, even during recovery.
    if plan.binding_mode == 'existing' and digest(plan.binding_path) != plan.input_hashes['binding']:
        raise ConfigError('stale_plan')
    return config


def preconditions(plan):
    for name, expected in plan.input_hashes.items():
        if name in ('policy', 'binding'):
            continue
        relative = '.harness/client.yaml' if name == 'descriptor' else name
        path = safe_path(Path(plan.target_path) / relative)
        if not path.exists() or digest(path) != expected:
            raise ConfigError('stale_plan')


def journal_path(state, run_id):
    try:
        identifier(run_id)
    except ValueError:
        raise ConfigError('invalid_run_id') from None
    return safe_path(Path(state) / 'onboarding' / run_id / 'journal.json')


def journal_matches(journal, plan):
    if (journal.client_id != plan.binding.client_id or journal.checkout_id != plan.binding.checkout_id or
        journal.target_path != plan.target_path or journal.binding_path != plan.binding_path or
        journal.policy_sha256 != plan.policy_sha256 or journal.plan_sha256 != plan.plan_sha256):
        raise ConfigError('foreign_journal')
    allowed = {(o.scope, o.path): o for o in plan.operations}
    seen = set()
    for entry in journal.operations:
        key = (entry.scope, entry.kind, entry.path.lower())
        if key in seen:
            raise ConfigError('invalid_journal')
        seen.add(key)
        if entry.kind == 'file':
            op = allowed.get((entry.scope, entry.path))
            if not op or entry.sha256 != op.sha256:
                raise ConfigError('invalid_journal')
        else:
            destination_path(entry.path)
            if entry.scope != 'target' or not any(o.scope == 'target' and o.path.startswith(entry.path + '/') for o in plan.operations):
                raise ConfigError('invalid_journal')
    file_keys = {(o.scope, o.path) for o in journal.operations if o.kind == 'file'}
    if file_keys != set(allowed):
        raise ConfigError('invalid_journal')


def paths_for(plan, entry):
    if entry.scope == 'target':
        return Path(plan.target_path), entry.path
    return Path(plan.binding_path).parent, Path(plan.binding_path).name


def owned_intact(tree, entry):
    opener = tree.directory if entry.kind == 'directory' else tree.file
    with opener(entry.path) as handle:
        if not entry.file_identity or handle.identity() != entry.file_identity:
            return False
        return entry.kind == 'directory' or sha(handle.read(128 * 1024)) == entry.sha256


def completed_result(plan, journal, probe_fn, idempotent=False):
    result, code = doctor(plan.target_path, plan.policy_path, plan.binding_path, probe_fn=probe_fn)
    result.update(command='init', application_status='completed', run_id=journal.run_id,
                  plan_sha256=plan.plan_sha256, idempotent=idempotent,
                  operations=[e.model_dump() for e in journal.operations])
    return result, code


def verify_completed(plan, journal):
    journal_matches(journal, plan)
    preconditions(plan)
    for entry in journal.operations:
        if entry.state != 'created':
            raise ConfigError('invalid_journal')
        root, relative = paths_for(plan, entry)
        effective = entry.model_copy(update={'path': relative})
        with PinnedTree(root) as tree:
            if not owned_intact(tree, effective):
                raise ConfigError('application_conflict')


def matching_runs(plan):
    state = safe_path(plan.binding.state_dir)
    parent = safe_path(state / 'onboarding')
    if not parent.exists():
        return []
    matches = []
    for folder in sorted(parent.iterdir()):
        path = safe_path(folder / 'journal.json')
        if path.exists():
            journal = load_json(path, Journal)
            if journal.run_id != folder.name:
                raise ConfigError('invalid_journal')
            # Never ignore foreign records inside this binding's state.
            if journal.client_id != plan.binding.client_id or journal.checkout_id != plan.binding.checkout_id or journal.target_path != plan.target_path:
                raise ConfigError('foreign_journal')
            if journal.plan_sha256 == plan.plan_sha256:
                journal_matches(journal, plan)
                if journal.state != 'recovered':
                    matches.append(journal)
            elif journal.state in ('in_progress', 'failed', 'recovery_conflict'):
                raise ConfigError('recovery_required')
    return matches


def apply(target, policy_path, plan_path, probe_fn=probe):
    # Pin the selected checkout and immutable inputs BEFORE validation. This
    # binds preflight and all later client writes to the same directory object.
    with ExitStack() as stack:
        stack.enter_context(PinnedTree(target))
        for path in (policy_path, plan_path):
            selected_path = absolute_path(str(safe_path(path)))
            tree = stack.enter_context(PinnedTree(selected_path.parent))
            stack.enter_context(tree.file(selected_path.name))
        plan = load_plan(plan_path)
        binding_tree = stack.enter_context(PinnedTree(Path(plan.binding_path).parent))
        if plan.binding_mode == 'existing':
            stack.enter_context(binding_tree.file(Path(plan.binding_path).name))
        return _apply(target, policy_path, plan_path, probe_fn)


def _apply(target, policy_path, plan_path, probe_fn):
    plan_path = absolute_path(str(safe_path(plan_path)))
    plan = load_plan(plan_path)
    separate([str(plan_path), plan.target_path, plan.policy_path, plan.binding_path, plan.binding.state_dir])
    selected(plan, target, policy_path)
    runs = matching_runs(plan)
    if runs:
        if len(runs) != 1 or runs[0].state != 'completed':
            raise ConfigError('recovery_required')
        state = safe_path(plan.binding.state_dir)
        with CheckoutLock(state, runs[0].run_id):
            verify_completed(plan, runs[0])
        return completed_result(plan, runs[0], probe_fn, idempotent=True)
    # Regeneration independently proves payload and complete operation selection.
    options = dict(repo=plan.descriptor.repository, base_branch=plan.descriptor.base_branch, probe_fn=probe_fn)
    if plan.binding_mode == 'proposed':
        options.update(binding_out=plan.binding_path, checkout_id=plan.binding.checkout_id,
                       state_dir=plan.binding.state_dir, databricks_profile=plan.binding.databricks_profile)
    else:
        options['binding_path'] = plan.binding_path
    regenerated, _ = preview(target, policy_path, **options)
    if regenerated['plan'] != plan.model_dump():
        raise ConfigError('stale_plan')
    preconditions(plan)
    if not Path(plan.binding_path).parent.is_dir():
        raise ConfigError('binding_parent_missing')
    state = ensure_state(plan.binding)
    run_id = uuid.uuid4().hex
    with CheckoutLock(state, run_id):
        # Another process could have completed between the read and lock.
        if matching_runs(plan):
            raise ConfigError('recovery_required')
        selected(plan, target, policy_path)
        preconditions(plan)
        for op in plan.operations:
            path = Path(plan.target_path) / op.path if op.scope == 'target' else Path(op.path)
            if safe_path(path).exists():
                raise ConfigError('stale_plan')
        with PinnedTree(state) as tree:
            if not (state / 'onboarding').exists():
                with tree.directory('onboarding', create=True):
                    pass
            with tree.directory('onboarding/' + run_id, create=True):
                pass
            with tree.file('onboarding/' + run_id + '/plan.json', create=True) as handle:
                handle.write(canonical(plan.model_dump()) + b'\n')
        path = journal_path(state, run_id)
        directories = set()
        for op in plan.operations:
            if op.scope == 'target':
                for parent in Path(op.path).parents:
                    if str(parent) != '.' and not safe_path(Path(plan.target_path) / parent).exists():
                        directories.add(parent.as_posix())
        entries = [JournalOperation(schema_version=1, scope='target', kind='directory', path=d, state='planned')
                   for d in sorted(directories, key=lambda p: (p.count('/'), p))]
        entries.extend(JournalOperation(schema_version=1, scope=o.scope, kind='file', path=o.path,
                                       state='planned', sha256=o.sha256) for o in plan.operations)
        journal = Journal(schema_version=1, client_id=plan.binding.client_id, checkout_id=plan.binding.checkout_id,
                          run_id=run_id, plan_sha256=plan.plan_sha256, target_path=plan.target_path,
                          binding_path=plan.binding_path, policy_sha256=plan.policy_sha256,
                          state='in_progress', operations=entries)
        persist(path, journal)  # No client writes until this succeeds.
        try:
            with ExitStack() as stack:
                trees = {'target': stack.enter_context(PinnedTree(plan.target_path)),
                         'binding': stack.enter_context(PinnedTree(Path(plan.binding_path).parent))}
                for entry in journal.operations:
                    entry.state = 'creating'
                    persist(path, journal)
                    tree = trees[entry.scope]
                    relative = entry.path if entry.scope == 'target' else Path(entry.path).name
                    opener = tree.directory if entry.kind == 'directory' else tree.file
                    with opener(relative, create=True) as handle:
                        if entry.kind == 'file':
                            op = next(o for o in plan.operations if o.scope == entry.scope and o.path == entry.path)
                            handle.write(op.content.encode('utf-8'))
                        entry.file_identity = handle.identity()
                        entry.state = 'created'
                        persist(path, journal)
                journal.state = 'completed'
                persist(path, journal)
        except (ConfigError, OSError) as error:
            # Reload durable evidence: an intent alone does not prove ownership.
            journal = load_json(path, Journal)
            journal.state = 'failed'
            persist(path, journal)
            error_code = error.code if isinstance(error, ConfigError) else 'application_failed'
            return report('init', [Check('application', 'error', error_code, 'Aplicación incompleta; revisar recuperación.')],
                          application_status='failed', run_id=run_id, plan_sha256=plan.plan_sha256,
                          operations=[e.model_dump() for e in journal.operations])
    return completed_result(plan, journal, probe_fn)


def recovery_inputs(target, policy_path, run_id, binding_path, plan_path):
    if bool(binding_path) == bool(plan_path):
        raise ConfigError('recovery_inputs_invalid')
    if plan_path:
        plan = load_plan(plan_path)
        separate([str(absolute_path(str(plan_path))), plan.target_path, plan.policy_path, plan.binding_path, plan.binding.state_dir])
        state = safe_path(plan.binding.state_dir)
    else:
        binding = load_document(binding_path, Binding)
        state = absolute_path(binding.state_dir)
        path = journal_path(state, run_id)
        plan = load_plan(path.parent / 'plan.json')
        if binding.model_dump() != plan.binding.model_dump() or safe_path(binding_path) != safe_path(plan.binding_path):
            raise ConfigError('foreign_journal')
    selected(plan, target, policy_path)
    path = journal_path(state, run_id)
    stored = load_plan(path.parent / 'plan.json')
    if stored.model_dump() != plan.model_dump():
        raise ConfigError('invalid_journal')
    journal = load_json(path, Journal)
    if journal.run_id != run_id:
        raise ConfigError('foreign_journal')
    journal_matches(journal, plan)
    return plan, journal, path


def recover(target, policy_path, run_id, *, binding_path=None, plan_path=None, apply_changes=False):
    with ExitStack() as stack:
        stack.enter_context(PinnedTree(target))
        selected_path = absolute_path(str(safe_path(policy_path)))
        tree = stack.enter_context(PinnedTree(selected_path.parent))
        stack.enter_context(tree.file(selected_path.name))
        if plan_path:
            selected_path = absolute_path(str(safe_path(plan_path)))
            tree = stack.enter_context(PinnedTree(selected_path.parent))
            stack.enter_context(tree.file(selected_path.name))
        return _recover(target, policy_path, run_id, binding_path=binding_path,
                        plan_path=plan_path, apply_changes=apply_changes)


def _recover(target, policy_path, run_id, *, binding_path=None, plan_path=None, apply_changes=False):
    plan, journal, path = recovery_inputs(target, policy_path, run_id, binding_path, plan_path)
    with ExitStack() as stack:
        if apply_changes:
            stack.enter_context(CheckoutLock(path.parents[2], run_id, recover=True))
            plan, journal, path = recovery_inputs(target, policy_path, run_id, binding_path, plan_path)
        trees = {'target': stack.enter_context(PinnedTree(plan.target_path)),
                 'binding': stack.enter_context(PinnedTree(Path(plan.binding_path).parent))}
        actions = []
        conflicts = False
        for entry in reversed(journal.operations):
            output = entry.model_copy()
            tree = trees[entry.scope]
            relative = entry.path if entry.scope == 'target' else Path(entry.path).name
            actual = safe_path(tree.root / relative)
            try:
                if entry.state in ('planned', 'removed'):
                    if entry.state == 'planned' and actual.exists():
                        raise ConfigError('recovery_conflict')
                    output.state = 'removed'
                elif not actual.exists():
                    # Missing files need no deletion, but missing creating operations
                    # are still safe to settle only as an absent result.
                    output.state = 'removed'
                elif entry.state not in ('created', 'conflict') or not entry.file_identity:
                    raise ConfigError('recovery_conflict')
                else:
                    opener = tree.directory if entry.kind == 'directory' else tree.file
                    with opener(relative, delete=apply_changes) as handle:
                        if handle.identity() != entry.file_identity:
                            raise ConfigError('recovery_conflict')
                        if entry.kind == 'file' and sha(handle.read(128 * 1024)) != entry.sha256:
                            raise ConfigError('recovery_conflict')
                        if entry.kind == 'directory' and any(actual.iterdir()):
                            # Preview anticipates removals of owned descendants below.
                            removable = {a['path'] for a in actions if a['state'] == 'removed' and a['scope'] == 'target'}
                            if apply_changes or any(p.relative_to(tree.root).as_posix() not in removable for p in actual.iterdir()):
                                raise ConfigError('recovery_conflict')
                        if apply_changes:
                            handle.delete()  # Empty-directory enforcement is native too.
                        output.state = 'removed'
            except (ConfigError, OSError):
                output.state = 'conflict'
                conflicts = True
            actions.append(output.model_dump())
            if apply_changes:
                entry.state = output.state
                persist(path, journal)
        if apply_changes:
            journal.state = 'recovery_conflict' if conflicts else 'recovered'
            persist(path, journal)
    return report('recover', [Check('recovery', 'error' if conflicts else 'ready',
                  'recovery_conflict' if conflicts else 'recovery_reviewed',
                  'Hay creaciones que requieren revisión manual.' if conflicts else 'Creaciones propias revisadas.')],
                  recovery_status=journal.state if apply_changes else 'preview', run_id=run_id,
                  plan_sha256=plan.plan_sha256, operations=actions)
