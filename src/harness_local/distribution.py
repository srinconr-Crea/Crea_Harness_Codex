"""Reviewable preparation and owned-file update, with no remote effects."""
from contextlib import ExitStack
from importlib.resources import files
import json
from pathlib import Path
import shutil
import uuid

from harness_core.configuration import ConfigError, safe_path, pairs
from harness_core.distribution import (ReleaseManifest, InstallationBinding, UpdatePlan,
    UpdateJournal, UpdateRecord, PilotReport, PROTOCOLS, managed_destination)
from harness_core.onboarding_plan import canonical, sha, load_json, separate, unmanaged_path
from .desktop_integration import selected, input_hashes, authorized
from .execution_state import CheckoutLock, ensure_state, persist
from .windows_fs import PinnedTree


def report(command, status='ready', **extra):
    return dict(schema_version=1, command=command, status=status, checks=[],
        certified=False, release_allowed=False, publication_allowed=False, **extra), (1 if status == 'blocked' else 0)


def candidate_manifest():
    root = files('harness_local')
    manifest = ReleaseManifest.model_validate(json.loads(root.joinpath('distribution_kit/candidate.json').read_bytes()))
    for path, expected in manifest.resources.items():
        resource=files('harness_core').joinpath(path[len('harness_core/'):]) if path.startswith('harness_core/') else root.joinpath(path)
        if sha(resource.read_bytes()) != expected:
            raise ConfigError('distribution_resource_drift')
    return manifest


def bootstrap(*, detect=shutil.which):
    manifest = candidate_manifest()
    commands = {'python': 'Python 3.13: revisar instalador y SHA oficial antes de ejecutarlo.',
        'git': 'Git: revisar versión/instalador Windows.',
        'node': 'Node/OpenSpec: revisar versión fijada por el proyecto.',
        'openspec': 'OpenSpec: preparar CLI por mecanismo revisado; no instala agentes.',
        'databricks': 'Databricks CLI: preparar por separado cuando el cliente lo requiera.'}
    steps=[]
    for name,instruction in commands.items():
        detected=bool(detect(name))
        steps.append(dict(tool=name,detected=detected,status='detected' if detected else 'missing',
            instruction=instruction,review_required=True))
    steps.append(dict(tool='harness', detected=True, status='candidate', review_required=True,
        instruction='Crear venv local Python 3.13; revisar wheelhouse/SHA y usar pip --no-index --require-hashes con runtime-lock.txt. Abrir checkout cliente en Desktop y ejecutar onboard --dry-run.'))
    return report('bootstrap', 'partial', steps=steps, login='pending', trust='pending',
        configuration='pending', plugin='unsupported', manifest_sha256=manifest.manifest_sha256)


def _content(tree, target, path):
    if not safe_path(target / path).exists(): return None, None
    with tree.file(path) as handle: return handle.read(128*1024), handle.identity()


def _edits(tree, target, installation, manifest, upstream):
    if not upstream or not set(upstream) <= set(installation.files):
        raise ConfigError('update_unowned_file')
    edits = []
    for path, content in sorted(upstream.items()):
        managed_destination(path)
        if sha(content.encode('utf-8')) not in manifest.resources.values():
            raise ConfigError('update_upstream_unpinned')
        raw, identity = _content(tree, target, path)
        local = sha(raw) if raw is not None else None
        edits.append(dict(schema_version=1, path=path, content=content,
            installed_hash=installation.files[path], local_hash=local, local_identity=identity,
            upstream_hash=sha(content.encode('utf-8')), backup=f'{len(edits):02d}.bak' if raw is not None else None,
            conflict=local != installation.files[path]))
    # The client lock is also owned, backed up and restored by the same journal.
    raw, identity = _content(tree, target, 'kit.lock.json')
    expected = canonical(installation.model_dump()) + b'\n'
    updated = installation.model_copy(update={'release_sha256': manifest.manifest_sha256,
        'files': {**installation.files, **{p: sha(c.encode('utf-8')) for p, c in upstream.items()}}})
    content = (canonical(updated.model_dump()) + b'\n').decode('utf-8')
    local = sha(raw) if raw is not None else None
    installed = sha(expected) if raw is not None else None
    edits.append(dict(schema_version=1, path='kit.lock.json', content=content, installed_hash=installed,
        local_hash=local, local_identity=identity, upstream_hash=sha(content.encode('utf-8')),
        backup=f'{len(edits):02d}.bak' if raw is not None else None, conflict=local != installed))
    return edits


def preview(target, policy_path, binding_path, installation, manifest, upstream, *, plan_out=None):
    target, config = selected(target, policy_path, binding_path)
    if safe_path(installation.binding_path) != safe_path(binding_path): raise ConfigError('update_identity_mismatch')
    with PinnedTree(target) as tree:
        edits = _edits(tree, target, installation, manifest, upstream)
        authorized(edits, config['policy'])
        value = dict(schema_version=1, run_id=uuid.uuid4().hex, target_path=str(target),
            target_identity=tree.base.identity(), policy_path=str(safe_path(policy_path)),
            binding_path=str(safe_path(binding_path)), input_hashes=input_hashes(target, policy_path, binding_path),
            installation=installation.model_dump(), manifest=manifest.model_dump(), edits=edits,
            applicable=not any(e['conflict'] for e in edits), kind='update_plan')
        plan = UpdatePlan.model_validate({**value, 'plan_sha256': sha(canonical(value))})
        if plan_out:
            out = unmanaged_path(str(safe_path(plan_out)))
            separate([str(out), str(target), str(policy_path), str(binding_path), config['binding'].state_dir])
            with PinnedTree(out.parent) as output:
                with output.file(out.name, create=True) as handle: handle.write(canonical(plan.model_dump()) + b'\n')
        return report('update-preview', 'ready' if plan.applicable else 'blocked', plan=plan.model_dump(),
            conflicts=[e.path for e in plan.edits if e.conflict])


def _validate(target, policy_path, plan_path):
    plan = load_json(plan_path, UpdatePlan)
    separate([str(safe_path(plan_path)), plan.target_path, plan.policy_path, plan.binding_path,
        json.loads(safe_path(plan.binding_path).read_bytes(), object_pairs_hook=pairs)['state_dir']])
    if safe_path(target) != safe_path(plan.target_path) or safe_path(policy_path) != safe_path(plan.policy_path):
        raise ConfigError('update_identity_mismatch')
    target, config = selected(target, policy_path, plan.binding_path)
    if input_hashes(target, policy_path, plan.binding_path) != plan.input_hashes:
        raise ConfigError('update_drift')
    if safe_path(plan.installation.binding_path) != safe_path(plan.binding_path): raise ConfigError('update_identity_mismatch')
    authorized([e.model_dump() for e in plan.edits], config['policy'])
    if not plan.applicable: raise ConfigError('update_conflict')
    upstream = {e.path:e.content for e in plan.edits if e.path != 'kit.lock.json'}
    if set(upstream) - set(plan.installation.files): raise ConfigError('update_unowned_file')
    for edit in plan.edits:
        if edit.path == 'kit.lock.json': continue
        managed_destination(edit.path)
        if edit.installed_hash != plan.installation.files[edit.path] or edit.upstream_hash not in plan.manifest.resources.values():
            raise ConfigError('update_upstream_unpinned')
    expected_lock = plan.installation.model_copy(update={'release_sha256': plan.manifest.manifest_sha256,
        'files': {**plan.installation.files, **{p:sha(c.encode('utf-8')) for p,c in upstream.items()}}})
    locks = [e for e in plan.edits if e.path == 'kit.lock.json']
    if len(locks) != 1 or locks[0].content.encode('utf-8') != canonical(expected_lock.model_dump())+b'\n':
        raise ConfigError('update_lock_invalid')
    expected_old=sha(canonical(plan.installation.model_dump())+b'\n') if locks[0].local_hash is not None else None
    if locks[0].installed_hash!=expected_old: raise ConfigError('update_lock_invalid')
    for i, edit in enumerate(plan.edits):
        if edit.backup != (f'{i:02d}.bak' if edit.local_hash is not None else None): raise ConfigError('update_backup_invalid')
        if (edit.local_hash is None)!=(edit.local_identity is None): raise ConfigError('update_identity_mismatch')
    return plan, target, config['binding']


def _pin_inputs(stack, plan, plan_path):
    for path in (plan_path, plan.policy_path, plan.binding_path, Path(plan.target_path)/'.harness/client.yaml'):
        path = safe_path(path)
        tree = stack.enter_context(PinnedTree(path.parent))
        stack.enter_context(tree.file(path.name))


def apply(target, policy_path, plan_path, *, activity_context=None):
    from .activity_execution import run,operation_key
    plan,selected_target,binding=_validate(target,policy_path,plan_path)
    if activity_context is None and ((Path(binding.state_dir)/'activity.sqlite3').exists() or Path(plan.binding_path+'.setup.json').exists()):
        activity_context=dict(schema_version=1,target_path=str(selected_target),policy_path=str(policy_path),
            binding_path=plan.binding_path,operation_id=plan.run_id)
    def execute():
        if activity_context:
            value=dict(plan_sha256=plan.plan_sha256,operation_key=operation_key(activity_context,'distribution_apply'))
            path=safe_path(binding.state_dir)/('update-activity-'+plan.run_id+'.json')
            with PinnedTree(path.parent) as tree:
                if path.exists():
                    with tree.file(path.name) as handle:
                        if handle.read()!=canonical(value): raise ConfigError('ledger_operation_conflict')
                else:
                    with tree.file(path.name,create=True) as handle: handle.write(canonical(value))
        return _apply(target,policy_path,plan_path)
    return run(activity_context,'distribution_apply',execute,expected_binding=binding,request_sha256=plan.plan_sha256)


def _apply(target, policy_path, plan_path):
    plan, target, binding = _validate(target, policy_path, plan_path)
    with ExitStack() as stack:
        tree = stack.enter_context(PinnedTree(target))
        _pin_inputs(stack, plan, plan_path)
        _validate(target, policy_path, plan_path)
        if tree.base.identity() != plan.target_identity: raise ConfigError('update_identity_mismatch')
        handles, originals = {}, {}
        for edit in plan.edits:
            if edit.local_hash is None:
                if safe_path(target/edit.path).exists(): raise ConfigError('update_drift')
            else:
                handle = stack.enter_context(tree.editable_file(edit.path))
                raw = handle.read(128*1024)
                if sha(raw) != edit.local_hash or handle.identity() != edit.local_identity: raise ConfigError('update_drift')
                handles[edit.path], originals[edit.path] = handle, raw
        state = ensure_state(binding)
        with CheckoutLock(state, plan.run_id):
            with PinnedTree(state) as external:
                with external.directory('update-'+plan.run_id, create=True): pass
            folder = state/('update-'+plan.run_id)
            with PinnedTree(folder) as external:
                with external.file('plan.json', create=True) as h: h.write(canonical(plan.model_dump()))
                for edit in plan.edits:
                    if edit.backup:
                        with external.file(edit.backup, create=True) as h: h.write(originals[edit.path])
                journal = UpdateJournal(schema_version=1, plan_sha256=plan.plan_sha256,
                    target_identity=plan.target_identity, state='prepared', records=[])
                journal_path = folder/'journal.json'
                persist(journal_path, journal)
                try:
                    for edit in plan.edits:
                        handle = handles.get(edit.path)
                        if handle is None: handle = stack.enter_context(tree.file(edit.path, create=True))
                        record = UpdateRecord(schema_version=1, path=edit.path, identity=handle.identity(), state='prepared')
                        journal.records.append(record)
                        persist(journal_path, journal)
                        if edit.local_hash is None: handle.write(edit.content.encode('utf-8'))
                        else: handle.replace_bytes(edit.content.encode('utf-8'))
                        record.state='applied'
                        persist(journal_path, journal)
                    journal.state='applied'
                    persist(journal_path, journal)
                except (ConfigError, OSError):
                    journal.state='failed'
                    persist(journal_path, journal)
                    return report('update-apply', 'blocked', run_id=plan.run_id, reason='update_failed')
    return report('update-apply', run_id=plan.run_id)


def recover(target, policy_path, plan_path, *, apply_changes=False, activity_context=None):
    from .activity_execution import run
    if activity_context is not None and not apply_changes: raise ConfigError('invalid_arguments')
    if not apply_changes: return _recover(target,policy_path,plan_path,apply_changes=False)
    plan,selected_target,binding=_validate(target,policy_path,plan_path)
    if activity_context is None and ((Path(binding.state_dir)/'activity.sqlite3').exists() or Path(plan.binding_path+'.setup.json').exists()):
        activity_context=dict(schema_version=1,target_path=str(selected_target),policy_path=str(policy_path),
            binding_path=plan.binding_path,operation_id=plan.run_id)
    def execute():
        result=_recover(target,policy_path,plan_path,apply_changes=True)
        link=safe_path(binding.state_dir)/('update-activity-'+plan.run_id+'.json')
        if activity_context and result[1]==0 and link.exists():
            with PinnedTree(link.parent) as tree:
                with tree.file(link.name) as handle: value=json.loads(handle.read(4096))
            if value['plan_sha256']!=plan.plan_sha256: raise ConfigError('ledger_operation_conflict')
            from .activity_ledger import ActivityLedger
            ActivityLedger(binding).finish_pending(value['operation_key'],'blocked')
        return result
    return run(activity_context,'distribution_recover',execute,
        expected_binding=binding,reconciler=True,reconcile_success=('ready',),request_sha256=plan.plan_sha256)


def _recover(target, policy_path, plan_path, *, apply_changes=False):
    plan, target, binding = _validate(target, policy_path, plan_path)
    folder = safe_path(binding.state_dir)/('update-'+plan.run_id)
    with ExitStack() as stack:
        tree = stack.enter_context(PinnedTree(target))
        external = stack.enter_context(PinnedTree(folder))
        _pin_inputs(stack, plan, plan_path)
        jh = stack.enter_context(external.file('journal.json'))
        journal = UpdateJournal.model_validate(json.loads(jh.read(), object_pairs_hook=pairs))
        frozen = sha(canonical(journal.model_dump()))
        if journal.plan_sha256 != plan.plan_sha256 or journal.target_identity != tree.base.identity():
            raise ConfigError('update_identity_mismatch')
        if journal.state == 'recovered': return report('update-recover', recovery_status='already_recovered')
        edits = {e.path:e for e in plan.edits}
        if len({r.path for r in journal.records}) != len(journal.records) or any(r.path not in edits for r in journal.records):
            raise ConfigError('update_journal_invalid')
        if journal.state == 'applied' and set(edits) != {r.path for r in journal.records}: raise ConfigError('update_journal_invalid')
        handles, backups, conflicts = {}, {}, []
        for record in journal.records:
            edit = edits[record.path]
            if edit.local_hash is None and not safe_path(target/edit.path).exists():
                record.state='recovered'
                continue
            handle = stack.enter_context(tree.editable_file(edit.path, delete=True))
            current = sha(handle.read(128*1024))
            if handle.identity() != record.identity:
                conflicts.append(edit.path)
                continue
            if edit.local_hash is not None and current == edit.local_hash:
                record.state='recovered'
                continue
            if current != edit.upstream_hash or record.state == 'recovered':
                conflicts.append(edit.path)
                continue
            handles[edit.path]=handle
            if edit.backup:
                with external.file(edit.backup) as backup: raw=backup.read(128*1024)
                if sha(raw) != edit.local_hash: conflicts.append(edit.path)
                else: backups[edit.path]=raw
        if conflicts: return report('update-recover', 'blocked', conflicts=conflicts)
        if not apply_changes: return report('update-recover', recovery_status='ready')
        jh.close()
        with CheckoutLock(binding.state_dir, plan.run_id, recover=True):
            _validate(target, policy_path, plan_path)
            if sha(canonical(load_json(folder/'journal.json', UpdateJournal).model_dump())) != frozen:
                raise ConfigError('update_drift')
            for record in reversed(journal.records):
                if record.state == 'recovered': continue
                edit = edits[record.path]
                if edit.backup: handles[edit.path].replace_bytes(backups[edit.path])
                else: handles[edit.path].delete()
                record.state='recovered'
                persist(folder/'journal.json', journal)
            journal.state='recovered'
            persist(folder/'journal.json', journal)
    return report('update-recover', recovery_status='recovered')


def _evidence(path, expected, root):
    if not path or not expected or root is None: raise ConfigError('acceptance_evidence_missing')
    from harness_core.onboarding_plan import destination_path
    destination_path(path)
    with PinnedTree(root) as tree:
        with tree.file(path) as handle: raw = handle.read()
    if sha(raw) != expected: raise ConfigError('acceptance_evidence_drift')
    return json.loads(raw, object_pairs_hook=pairs)


def release_gate(pilot, *, evidence_root=None):
    """Validate imported human evidence; hashes provide integrity, not signatures."""
    manifest = candidate_manifest()
    pending = []
    if pilot.candidate_sha256 != manifest.manifest_sha256: pending.append('candidate_mismatch')
    if pilot.implementation_status != 'complete': pending.append('implementation_incomplete')
    receipts = {r.protocol:r for r in pilot.receipts}
    for protocol in PROTOCOLS:
        receipt = receipts.get(protocol)
        if receipt is None or receipt.status != 'passed' or receipt.source != 'desktop_harness':
            pending.append(protocol)
            continue
        try:
            value = _evidence(receipt.evidence_path, receipt.evidence_sha256, evidence_root)
            if (value.get('candidate_sha256') != pilot.candidate_sha256 or value.get('protocol') != protocol
                or value.get('status') != 'passed' or value.get('source') != 'desktop_harness'
                or value.get('simulated') is not False): raise ConfigError('acceptance_receipt_invalid')
        except (ConfigError, ValueError, OSError): pending.append(protocol)
    profiles=[]
    try:
        from .evaluation_service import dispatch
        evaluation = _evidence(pilot.evaluation_path, pilot.evaluation_sha256, evidence_root)
        result, code = dispatch('report', evaluation)
        profiles=evaluation.get('profiles',[])
        if (evaluation.get('milestone') != 7 or evaluation.get('purpose') != 'promotion'
            or result['required_runs'] != 144 or code or len(profiles)!=2
            or {p.get('profile_id') for p in profiles}!={'baseline','candidate'}
            or any(p.get('surface')!='desktop' or p.get('model')!='luna' or p.get('effort')!='medium' for p in profiles)):
            pending.append('required_real_evals')
    except (ConfigError, ValueError, OSError): pending.append('required_real_evals')
    try:
        from harness_core.desktop import RoleCatalog, DesktopCertificate, assess_certificate
        catalog = RoleCatalog.model_validate(_evidence(pilot.catalog_path, pilot.catalog_sha256, evidence_root))
        certificate = DesktopCertificate.model_validate(_evidence(pilot.certificate_path, pilot.certificate_sha256, evidence_root))
        if not assess_certificate(catalog, certificate)['certified']: pending.append('desktop_certificate')
        practice_sha=sha(files('harness_local').joinpath('quality_kit/practices.json').read_bytes())
        if any(p.get('roles_sha256')!=catalog.sha256 or p.get('practices_sha256')!=practice_sha
            or p.get('runtime')!=certificate.app_version or not p.get('configuration_evidence_ref') for p in profiles):
            pending.append('eval_configuration_mismatch')
        if any((r.model,r.effort)!=('luna','medium') for r in catalog.roles if r.activated):
            pending.append('eval_configuration_mismatch')
        for profile in profiles:
            ref=profile.get('configuration_evidence_ref')
            configuration=_evidence(str(ref)+'.json',pilot.configuration_evidence.get(ref),evidence_root)
            if (sha(canonical(configuration))!=profile.get('config_sha256')
                or configuration.get('candidate_sha256')!=pilot.candidate_sha256
                or configuration.get('engine_version')!=certificate.engine_version
                or any(configuration.get(k)!=profile.get(k) for k in
                    ('model','effort','surface','runtime','roles_sha256','practices_sha256','tools'))):
                pending.append('eval_configuration_mismatch')
    except (ConfigError, ValueError, OSError): pending.append('desktop_certificate')
    allowed = not pending
    return dict(schema_version=1, command='release', status='ready' if allowed else 'blocked', checks=[],
        implementation_status=pilot.implementation_status, acceptance_status='accepted' if allowed else 'pending',
        candidate_sha256=pilot.candidate_sha256, certified=allowed, release_allowed=allowed,
        next_increment_enabled=allowed, publication_allowed=False, pending=sorted(set(pending))), (0 if allowed else 1)
