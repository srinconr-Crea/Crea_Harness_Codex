"""Bounded candidate hashing; detects persistent changes, never prevents edits."""
from contextlib import ExitStack
from harness_core.configuration import ConfigError, safe_path
from harness_core.supervised import CandidateEntry, CandidateSnapshot, evidence_digest, assess_preparation
from harness_core.desktop import IntegrationJournal
from harness_core.onboarding_plan import canonical, sha, destination_path, denied, load_json
from .desktop_integration import selected, input_hashes
from .windows_fs import PinnedTree

PROTECTED = ['.git/', '.codex/', '.agents/', '.harness/', 'evidence/']
FILE_LIMIT = 2 * 1024 * 1024
TOTAL_LIMIT = 16 * 1024 * 1024


def capture(target, policy_path, binding_path, scopes, catalog_sha256, certificate):
    target, config = selected(target, policy_path, binding_path)
    if certificate.catalog_sha256 != catalog_sha256:
        raise ConfigError('supervised_evidence_mismatch')
    scopes = sorted(scopes)
    if not 1 <= len(scopes) <= 32:
        raise ConfigError('invalid_candidate_scope')
    for index, scope in enumerate(scopes):
        destination_path(scope)
        if denied(scope, PROTECTED + config['policy'].denied_paths):
            raise ConfigError('candidate_scope_denied')
        if any(scope.lower() == other.lower() or scope.lower().startswith(other.lower() + '/') or
               other.lower().startswith(scope.lower() + '/') for other in scopes[:index]):
            raise ConfigError('invalid_candidate_scope')
        # Reject traversal through an existing file even when the leaf is absent.
        p = safe_path(target / scope)
        if any(parent.exists() and not parent.is_dir() for parent in p.parents if parent != target and target in parent.parents):
            raise ConfigError('invalid_candidate_scope')
    initial = input_hashes(target, policy_path, binding_path)
    configuration_sha256 = sha(canonical(initial))
    entries = []
    total = 0
    with ExitStack() as stack:
        tree = stack.enter_context(PinnedTree(target))
        listings = {}
        absences = []

        def walk(relative):
            nonlocal total
            destination_path(relative)
            if denied(relative, PROTECTED + config['policy'].denied_paths):
                raise ConfigError('candidate_scope_denied')
            if len(entries) >= 256:
                raise ConfigError('candidate_too_large')
            path = safe_path(target / relative)
            if not path.exists():
                # Pin every existing ancestor, so a replacement cannot redirect reads.
                parts = relative.split('/')
                for i in range(1, len(parts)):
                    if (target / '/'.join(parts[:i])).exists():
                        stack.enter_context(tree.directory('/'.join(parts[:i])))
                entries.append(CandidateEntry(schema_version=1, path=relative, kind='absent', identity=None, content_sha256=None))
                absences.append(path)
            elif path.is_dir():
                handle = stack.enter_context(tree.directory(relative))
                entries.append(CandidateEntry(schema_version=1, path=relative, kind='directory', identity=handle.identity(), content_sha256=None))
                children = sorted(path.iterdir(), key=lambda p: p.name)
                listings[path] = [p.name for p in children]
                for child in children:
                    walk(relative + '/' + child.name)
            else:
                handle = stack.enter_context(tree.file(relative))
                raw = handle.read(FILE_LIMIT)
                total += len(raw)
                if total > TOTAL_LIMIT:
                    raise ConfigError('candidate_too_large')
                entries.append(CandidateEntry(schema_version=1, path=relative, kind='file', identity=handle.identity(), content_sha256=sha(raw)))

        for scope in scopes:
            walk(scope)
        if any(p.exists() for p in absences) or any(sorted(p.name for p in folder.iterdir()) != names for folder, names in listings.items()):
            raise ConfigError('candidate_changed_during_capture')
        if input_hashes(target, policy_path, binding_path) != initial:
            raise ConfigError('supervised_identity_mismatch')
        return CandidateSnapshot(schema_version=1, client_id=config['binding'].client_id,
            checkout_id=config['binding'].checkout_id, target_path=str(target), target_identity=tree.base.identity(),
            catalog_sha256=catalog_sha256, evidence_sha256=evidence_digest(certificate),
            configuration_sha256=configuration_sha256, scopes=scopes, entries=entries)


def compare(target, policy_path, binding_path, before, certificate):
    after = capture(target, policy_path, binding_path, before.scopes, before.catalog_sha256, certificate)
    identity_fields = ('client_id', 'checkout_id', 'target_identity', 'configuration_sha256', 'evidence_sha256')
    if safe_path(before.target_path) != safe_path(after.target_path) or any(getattr(before, key) != getattr(after, key) for key in identity_fields):
        raise ConfigError('supervised_identity_mismatch')
    previous = {e.path: e.model_dump() for e in before.entries}
    current = {e.path: e.model_dump() for e in after.entries}
    differences = [dict(path=p, before=previous.get(p), after=current.get(p))
        for p in sorted(previous.keys() | current.keys()) if previous.get(p) != current.get(p)]
    return dict(schema_version=1, command='candidate-compare', status='blocked' if differences else 'ready',
        intact=not differences, before_sha256=before.sha256, after_sha256=after.sha256,
        differences=differences, checks=[], certified=False,
        limitation='Detects persistent changes within selected scopes; does not prevent writes or detect restored edits.')


def prepare(target, policy_path, binding_path, plan_path, catalog, certificate, snapshot, acceptance, *, required=()):
    from .desktop_integration import validate_plan, run_folder
    plan, target = validate_plan(target, policy_path, plan_path)
    if safe_path(binding_path) != safe_path(plan.binding_path) or plan.catalog != catalog:
        raise ConfigError('supervised_identity_mismatch')
    journal = load_json(run_folder(plan) / 'journal.json', IntegrationJournal)
    if journal.state != 'applied' or journal.plan_sha256 != plan.plan_sha256:
        raise ConfigError('integration_not_applied')
    records = {r.path: r for r in journal.records if r.kind == 'file'}
    if set(records) != {e.path for e in plan.edits}:
        raise ConfigError('integration_drift')
    with ExitStack() as stack:
        tree = stack.enter_context(PinnedTree(target))
        if journal.target_identity != tree.base.identity() or journal.client_id != plan.binding.client_id or journal.checkout_id != plan.binding.checkout_id:
            raise ConfigError('supervised_identity_mismatch')
        for edit in plan.edits:
            handle = stack.enter_context(tree.file(edit.path))
            if records[edit.path].state != 'applied' or handle.identity() != records[edit.path].identity or sha(handle.read(128 * 1024)) != edit.new_hash:
                raise ConfigError('integration_drift')
        comparison = compare(target, policy_path, binding_path, snapshot, certificate)
        result = assess_preparation(catalog, certificate, snapshot, acceptance, required=required)
        result['candidate_comparison'] = comparison
        if not comparison['intact']:
            result.update(prepared=False, status='blocked')
        return result
