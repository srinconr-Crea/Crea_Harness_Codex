"""Explicit project edits with external backups and conservative Windows recovery.

This adapter never calls Codex, authenticates, enables hooks or certifies Desktop.
It has an independent journal; onboarding v1 remains create-only.
"""
from contextlib import ExitStack
import json
from pathlib import Path
import tomllib
import uuid

from harness_core.configuration import ConfigError, digest, safe_path, validate_configuration, reject_secrets
from harness_core.desktop import DesktopIntegrationPlan, IntegrationJournal, IntegrationRecord
from harness_core.onboarding_plan import canonical, sha, load_json, separate, unmanaged_path, denied
from .desktop_resources import render_integration, resource_digest
from .diagnostics import checkout
from .execution_state import CheckoutLock, ensure_state, persist
from .windows_fs import PinnedTree


def report(command, status='ready', **extra):
    return dict(schema_version=1, command=command, status=status, checks=[], desktop_status='not_checked', **extra), (1 if status == 'blocked' else 0)


def authorized(edits, policy):
    if len(edits) > policy.max_files or sum(len(e['content'].encode('utf-8')) for e in edits) > policy.max_bytes:
        raise ConfigError('integration_policy_blocked')
    for edit in edits:
        if denied(edit['path'], policy.denied_paths + policy.read_only_paths):
            raise ConfigError('integration_policy_blocked')


def selected(target, policy_path, binding_path):
    target = unmanaged_path(str(safe_path(target)))
    policy_path = safe_path(policy_path)
    binding_path = unmanaged_path(str(safe_path(binding_path)))
    _, origin = checkout(target)
    config = validate_configuration(target, policy_path, binding_path, origin)
    separate([str(target), str(policy_path), str(binding_path), config['binding'].state_dir])
    unmanaged_path(config['binding'].state_dir)
    return target, config


def input_hashes(target, policy_path, binding_path):
    return dict(policy=digest(policy_path), binding=digest(binding_path), descriptor=digest(target / '.harness/client.yaml'))


def merge_content(path, old, proposed):
    if old is None:
        return proposed
    try:
        text = old.decode('utf-8')
        if path == 'AGENTS.md':
            if '<!-- harness-desktop-v1 -->' in text:
                raise ConfigError('integration_conflict')
        elif path == '.codex/config.toml':
            current = tomllib.loads(text)
            reject_secrets(current)
            added = tomllib.loads(proposed)
            agents = current.get('agents', {})
            if not isinstance(agents, dict) or set(agents) & set(added['agents']):
                raise ConfigError('integration_conflict')
            if any(key.startswith('harness-') for key in agents):
                raise ConfigError('integration_conflict')
            merged = text + '\n\n' + proposed
            tomllib.loads(merged)
        else:
            # An existing owned file is a personalization conflict, even if similar.
            raise ConfigError('integration_conflict')
        return text + '\n\n' + proposed
    except (UnicodeError, tomllib.TOMLDecodeError):
        raise ConfigError('integration_conflict') from None


def preview(target, policy_path, binding_path, catalog, *, plan_out=None):
    target, config = selected(target, policy_path, binding_path)
    content = render_integration(catalog)
    run_id = uuid.uuid4().hex
    edits = []
    # Pin all parents and originals for a coherent read-only snapshot.
    with ExitStack() as stack:
        tree = stack.enter_context(PinnedTree(target))
        for path, proposed in content.items():
            selected_path = safe_path(target / path)
            old = None
            identity = None
            if selected_path.exists():
                handle = stack.enter_context(tree.file(path))
                old, identity = handle.read(128 * 1024), handle.identity()
            merged = merge_content(path, old, proposed)
            reject_secrets(merged)
            if len(merged.encode('utf-8')) > 128 * 1024:
                raise ConfigError('document_too_large')
            edits.append(dict(schema_version=1, path=path, owner='harness-desktop-v1', content=merged,
                old_hash=sha(old) if old is not None else None, old_identity=identity, new_hash=sha(merged.encode('utf-8')),
                backup=f'{len(edits):02d}.bak' if old is not None else None))
        authorized(edits, config['policy'])
        value = dict(schema_version=1, kind='desktop_integration_plan', run_id=run_id,
            target_path=str(target), target_identity=tree.base.identity(), policy_path=str(safe_path(policy_path)),
            binding_path=str(safe_path(binding_path)), binding=config['binding'].model_dump(),
            input_hashes=input_hashes(target, policy_path, binding_path), catalog=catalog.model_dump(),
            resource_sha256=resource_digest(), edits=edits)
        plan = DesktopIntegrationPlan.model_validate({**value, 'plan_sha256': sha(canonical(value))})
        if plan_out is not None:
            out = unmanaged_path(str(safe_path(plan_out)))
            separate([str(out), str(target), str(policy_path), str(binding_path), plan.binding.state_dir])
            with PinnedTree(out.parent) as output:
                with output.file(out.name, create=True) as handle:
                    handle.write(canonical(plan.model_dump()) + b'\n')
        return report('integrate-preview', plan=plan.model_dump())


def validate_plan(target, policy_path, plan_path):
    plan = load_json(plan_path, DesktopIntegrationPlan)
    separate([str(safe_path(plan_path)), plan.target_path, plan.policy_path, plan.binding_path, plan.binding.state_dir])
    if safe_path(target) != safe_path(plan.target_path) or safe_path(policy_path) != safe_path(plan.policy_path):
        raise ConfigError('integration_identity_mismatch')
    target, config = selected(target, policy_path, plan.binding_path)
    if config['binding'] != plan.binding or input_hashes(target, policy_path, plan.binding_path) != plan.input_hashes:
        raise ConfigError('integration_drift')
    if resource_digest() != plan.resource_sha256:
        raise ConfigError('desktop_resources_invalid')
    rendered = render_integration(plan.catalog)
    if set(rendered) != {e.path for e in plan.edits}:
        raise ConfigError('integration_plan_invalid')
    authorized([e.model_dump() for e in plan.edits], config['policy'])
    return plan, target


def pin_inputs(stack, plan, plan_path):
    for path in (plan_path, plan.policy_path, plan.binding_path, Path(plan.target_path) / '.harness/client.yaml'):
        path = safe_path(path)
        tree = stack.enter_context(PinnedTree(path.parent))
        stack.enter_context(tree.file(path.name))


def run_folder(plan):
    return Path(plan.binding.state_dir) / ('desktop-' + plan.run_id)


def apply(target, policy_path, plan_path):
    plan, target = validate_plan(target, policy_path, plan_path)
    rendered = render_integration(plan.catalog)
    with ExitStack() as stack:
        tree = stack.enter_context(PinnedTree(target))
        pin_inputs(stack, plan, plan_path)
        validate_plan(target, policy_path, plan_path)
        if tree.base.identity() != plan.target_identity:
            raise ConfigError('integration_identity_mismatch')
        handles, originals = {}, {}
        for edit in plan.edits:
            path = safe_path(target / edit.path)
            if edit.old_hash is None:
                if path.exists():
                    raise ConfigError('integration_drift')
                if edit.content != rendered[edit.path]:
                    raise ConfigError('integration_plan_invalid')
            else:
                if not path.exists():
                    raise ConfigError('integration_drift')
                handle = stack.enter_context(tree.editable_file(edit.path))
                old = handle.read(128 * 1024)
                if sha(old) != edit.old_hash or handle.identity() != edit.old_identity:
                    raise ConfigError('integration_drift')
                if merge_content(edit.path, old, rendered[edit.path]) != edit.content:
                    raise ConfigError('integration_plan_invalid')
                handles[edit.path], originals[edit.path] = handle, old
        # No target or external state writes until every planned edit is checked.
        state = ensure_state(plan.binding)
        stack.enter_context(PinnedTree(state))
        with CheckoutLock(state, plan.run_id):
            with PinnedTree(state) as state_tree:
                with state_tree.directory('desktop-' + plan.run_id, create=True):
                    pass
            folder = run_folder(plan)
            with PinnedTree(folder) as external:
                with external.file('plan.json', create=True) as handle:
                    handle.write(canonical(plan.model_dump()))
                for edit in plan.edits:
                    if edit.backup:
                        with external.file(edit.backup, create=True) as handle:
                            handle.write(originals[edit.path])
                journal = IntegrationJournal(schema_version=1, client_id=plan.binding.client_id,
                    checkout_id=plan.binding.checkout_id, plan_sha256=plan.plan_sha256,
                    target_identity=plan.target_identity, state='prepared', records=[])
                journal_path = folder / 'journal.json'
                persist(journal_path, journal)
                try:
                    for edit in plan.edits:
                        parts = edit.path.split('/')
                        for i in range(1, len(parts)):
                            relative = '/'.join(parts[:i])
                            if not (target / relative).exists():
                                with tree.directory(relative, create=True) as handle:
                                    journal.records.append(IntegrationRecord(schema_version=1, path=relative,
                                        kind='directory', identity=handle.identity(), state='applied'))
                                    persist(journal_path, journal)
                        if edit.old_hash is None:
                            with tree.file(edit.path, create=True) as handle:
                                record = IntegrationRecord(schema_version=1, path=edit.path, kind='file', identity=handle.identity(), state='prepared')
                                journal.records.append(record)
                                persist(journal_path, journal)
                                handle.write(edit.content.encode('utf-8'))
                                record.state = 'applied'
                        else:
                            record = IntegrationRecord(schema_version=1, path=edit.path, kind='file', identity=handles[edit.path].identity(), state='prepared')
                            journal.records.append(record)
                            persist(journal_path, journal)
                            handles[edit.path].replace_bytes(edit.content.encode('utf-8'))
                            record.state = 'applied'
                        persist(journal_path, journal)
                    journal.state = 'applied'
                    persist(journal_path, journal)
                except (ConfigError, OSError):
                    journal.state = 'failed'
                    persist(journal_path, journal)
                    return report('integrate-apply', 'blocked', run_id=plan.run_id, code='integration_failed')
            return report('integrate-apply', run_id=plan.run_id)


def recover(target, policy_path, plan_path, *, apply_changes=False):
    plan, target = validate_plan(target, policy_path, plan_path)
    folder = run_folder(plan)
    journal_path = folder / 'journal.json'
    with ExitStack() as stack:
        tree = stack.enter_context(PinnedTree(target))
        external = stack.enter_context(PinnedTree(folder))
        pin_inputs(stack, plan, plan_path)
        # Pin the atomic journal snapshot through the entire preflight.
        journal_handle = stack.enter_context(external.file('journal.json'))
        journal = load_json(journal_path, IntegrationJournal)
        journal_snapshot = sha(canonical(journal.model_dump()))
        if (journal.client_id != plan.binding.client_id or journal.checkout_id != plan.binding.checkout_id or
            journal.plan_sha256 != plan.plan_sha256 or journal.target_identity != tree.base.identity()):
            raise ConfigError('integration_identity_mismatch')
        if journal.state == 'recovered':
            return report('integrate-recover', recovery_status='already_recovered')
        edits = {e.path: e for e in plan.edits}
        files, backups, directories = {}, {}, []
        conflicts = []
        seen = set()
        for record in journal.records:
            if record.path in seen:
                raise ConfigError('integration_journal_invalid')
            seen.add(record.path)
            if record.kind == 'directory':
                if not any(e.path.startswith(record.path + '/') for e in plan.edits):
                    raise ConfigError('integration_journal_invalid')
                directories.append(record)
                continue
            if record.path not in edits:
                raise ConfigError('integration_journal_invalid')
            edit = edits[record.path]
            # Removal is idempotent; absence cannot overwrite a user file.
            if edit.old_hash is None and not safe_path(target / record.path).exists():
                record.state = 'recovered'
                continue
            try:
                handle = stack.enter_context(tree.editable_file(record.path, delete=True))
                current = sha(handle.read(128 * 1024))
                if handle.identity() != record.identity:
                    conflicts.append(record.path)
                    continue
                # A restore may have completed before persisting its record.
                # The original bytes in the same owned object prove recovery.
                if edit.old_hash is not None and current == edit.old_hash:
                    record.state = 'recovered'
                    continue
                if current != edit.new_hash or record.state == 'recovered':
                    conflicts.append(record.path)
                    continue
                files[record.path] = handle
                if edit.backup:
                    backup = stack.enter_context(external.file(edit.backup))
                    raw = backup.read(128 * 1024)
                    if sha(raw) != edit.old_hash:
                        conflicts.append(record.path)
                    else:
                        backups[record.path] = raw
            except ConfigError:
                conflicts.append(record.path)
        if journal.state == 'applied' and {r.path for r in journal.records if r.kind == 'file'} != set(edits):
            conflicts.append('journal')
        # Directory identity is ownership evidence; user files prevent deletion.
        for record in directories:
            try:
                handle = stack.enter_context(tree.directory(record.path))
                if handle.identity() != record.identity:
                    conflicts.append(record.path)
            except ConfigError:
                conflicts.append(record.path)
        if conflicts:
            return report('integrate-recover', 'blocked', conflicts=sorted(set(conflicts)))
        if not apply_changes:
            return report('integrate-recover', recovery_status='ready')
        # Close journal read handle to permit atomic journal updates.
        journal_handle.close()
        with CheckoutLock(plan.binding.state_dir, plan.run_id, recover=True):
            validate_plan(target, policy_path, plan_path)
            original_journal = load_json(journal_path, IntegrationJournal)
            if sha(canonical(original_journal.model_dump())) != journal_snapshot:
                raise ConfigError('integration_drift')
            for record in reversed(journal.records):
                if record.kind != 'file' or record.state == 'recovered':
                    continue
                edit = edits[record.path]
                if edit.backup:
                    files[record.path].replace_bytes(backups[record.path])
                else:
                    files[record.path].delete()
                record.state = 'recovered'
                persist(journal_path, journal)
            # Handles hold directories through recovery. Leave created empty
            # directories: removing shared directories adds no product benefit.
            journal.state = 'recovered'
            persist(journal_path, journal)
        return report('integrate-recover', recovery_status='recovered')
