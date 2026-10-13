"""Reviewed staged onboarding. No global config, authentication or remote actions."""
from contextlib import ExitStack
import json
from pathlib import Path
import uuid

from pydantic import ValidationError

from harness_core.configuration import ConfigError, digest, load_document, safe_path
from harness_core.contracts import Policy
from harness_core.guided import (collect, GuidedRequest, QuestionnaireDraft, CompositePreparationPlan,
    GuidedOnboardingPlan, OnboardingRun, StageRecord, OperationRecord, sanitize)
from harness_core.onboarding_plan import Operation, canonical, sha, authorize, load_json, separate, unmanaged_path
from . import application, desktop_integration, guided_resources, supervised
from .desktop_resources import render_integration, resource_digest as desktop_digest
from .diagnostics import probe
from .execution_state import CheckoutLock, ensure_state, persist
from .onboarding import preview as init_preview
from .windows_fs import PinnedTree


def checkpoint(point):
    """Fault-injection seam; production has no effect."""


def parse(model, value):
    sanitize(value)
    try: return model.model_validate(value)
    except ValidationError: raise ConfigError('invalid_guided_document') from None


def export(path, value, selected_paths):
    out = unmanaged_path(str(safe_path(path)))
    separate([str(out), *selected_paths])
    sanitize(value)
    if out.exists(): raise ConfigError('export_exists')
    with PinnedTree(out.parent) as tree:
        with tree.file(out.name, create=True) as handle: handle.write(canonical(value) + b'\n')


def serialized(value): return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n'


def discover(draft):
    """Observed facts are suggestions, never permission or confirmed answers."""
    collected = collect(draft)
    target_value = collected['values'].get('target_path')
    if not target_value: return []
    from .diagnostics import checkout
    from harness_core.contracts import Descriptor
    from harness_core.configuration import normalize_remote
    target, origin = checkout(target_value)
    facts = [dict(field='repository',value=normalize_remote(origin),source='local',confirmed=False)]
    descriptor = safe_path(target/'.harness/client.yaml')
    if descriptor.exists():
        parsed = load_document(descriptor,Descriptor)
        facts.extend(dict(field=k,value=getattr(parsed,k),source='local',confirmed=False) for k in ('client_id','base_branch'))
    for name, stack in [('pyproject.toml','Python'),('package.json','Node'),('Cargo.toml','Rust')]:
        if safe_path(target/name).is_file(): facts.append(dict(field='stack',value=stack,source='local',confirmed=False))
    return facts


def context_content(development):
    parts = ['# Contexto del cliente: ' + development.client_id,
        'Configuración revisada; no otorga permisos ni autoriza ejecución remota.']
    for title, field in [('Stack', 'stack'), ('Convenciones', 'conventions'), ('Reglas de negocio', 'business_rules'), ('Validaciones', 'validations')]:
        parts.extend(['\n## ' + title, *('- ' + x for x in getattr(development, field))])
    parts.extend(['\n## Procedencia', serialized(development.sources)])
    return '\n'.join(parts) + '\n'


def options(request, *, existing=False):
    kw = dict(repo=request.repository, base_branch=request.base_branch)
    if request.binding_mode == 'proposed' and not existing:
        kw.update(binding_out=request.binding_path, checkout_id=request.tool_binding.checkout_id, state_dir=request.state_dir)
    else: kw['binding_path'] = request.binding_path
    return kw


def external_paths(plan):
    request = plan.request
    return [request.target_path, request.policy_path, request.binding_path, plan.preparation.binding.state_dir,
        *([request.development_policy_path] if request.development_policy_path and safe_path(request.development_policy_path) != safe_path(request.policy_path) else [])]


def tool_path(preparation):
    return str(Path(preparation.binding_path).with_name(Path(preparation.binding_path).name + '.tools.json'))


def preview(draft, *, probe_fn=probe, plan_out=None):
    bundle = guided_resources.resources()  # Dependency gate before all effects.
    collected = collect(draft)
    facts = discover(draft)
    collected['discovered_facts'] = facts
    if collected['questions']: return collected, 1
    request = parse(GuidedRequest, dict(schema_version=1, **collected['values']))
    if request.binding_mode == 'proposed' and (not request.repository or not request.base_branch):
        collected.update(status='blocked', questions=[dict(field=k, requirement='required', reason='missing_decision')
            for k in ('repository', 'base_branch') if not getattr(request, k)])
        return collected, 1
    base, _ = init_preview(request.target_path, request.policy_path, probe_fn=probe_fn, **options(request))
    from harness_core.onboarding_plan import OnboardingPlan
    initial = OnboardingPlan.model_validate(base['plan'])
    if request.development.client_id != initial.binding.client_id or request.tool_binding.checkout_id != initial.binding.checkout_id:
        raise ConfigError('client_mismatch')
    policy = load_document(request.policy_path, Policy)
    development_hash = None
    if request.development_policy_path:
        development_policy = load_document(request.development_policy_path, Policy)
        if (development_policy.client_id, development_policy.repository.lower(), development_policy.base_branch) != (
            policy.client_id, policy.repository.lower(), policy.base_branch): raise ConfigError('client_mismatch')
        development_hash = digest(request.development_policy_path)
    operations = list(initial.operations)
    hashes = dict(initial.input_hashes)
    blockers = []
    # The only init conflict this adapter can resolve is personalized instructions.
    blockers.extend('init_conflict:' + a['path'] for a in base['actions'] if a['status'] == 'conflict' and a['path'] != 'AGENTS.md')
    if any(c['status'] != 'ready' for c in base['checks'] if c['id'] in ('python', 'git')):
        blockers.append('required_local_tool_unavailable')
    additions = {
        '.harness/development.yaml': serialized(request.development.model_dump()),
        '.harness/context.md': context_content(request.development),
        '.agents/skills/harness-client-onboarding/SKILL.md': bundle['harness-client-onboarding/SKILL.md'],
    }
    target = safe_path(request.target_path)
    with ExitStack() as stack:
        tree = stack.enter_context(PinnedTree(target))
        for path, content in additions.items():
            existing = safe_path(target / path)
            if existing.exists():
                handle = stack.enter_context(tree.file(path)); raw = handle.read(128 * 1024)
                hashes[path] = sha(raw)
                if raw != content.encode('utf-8'): blockers.append('existing_resource_conflict:' + path)
            else: operations.append(Operation(schema_version=1, scope='target', path=path, content=content, sha256=sha(content.encode())))
        local = unmanaged_path(tool_path(initial))
        separate([str(local), *[initial.target_path, initial.policy_path, initial.binding_path, initial.binding.state_dir]])
        tool_content = serialized(request.tool_binding.model_dump())
        if local.exists():
            local_tree = stack.enter_context(PinnedTree(local.parent))
            handle = stack.enter_context(local_tree.file(local.name)); raw = handle.read(128 * 1024)
            hashes['tools'] = sha(raw)
            if raw != tool_content.encode('utf-8'): blockers.append('existing_tool_binding_conflict')
        else: operations.append(Operation(schema_version=1, scope='binding', path=str(local), content=tool_content, sha256=sha(tool_content.encode())))
        operations.sort(key=lambda o: (o.scope == 'binding', o.path.lower()))
        denial = authorize(operations, policy)
        if denial: blockers.append(denial)
        value = initial.model_dump(exclude={'plan_sha256'})
        value.update(kind='composite_preparation_plan', input_hashes=hashes,
            absent_paths=sorted(o.path for o in operations if o.scope == 'target'),
            operations=[o.model_dump() for o in operations], applicable=not blockers)
        preparation = CompositePreparationPlan.model_validate(dict(value, plan_sha256=sha(canonical(value))))
        edits = []
        proposed = {o.path:o.content for o in operations if o.scope == 'target'}
        try:
            for path, content in render_integration(request.catalog).items():
                old, identity = None, None
                actual = safe_path(target / path)
                if actual.exists():
                    handle = stack.enter_context(tree.file(path)); old, identity = handle.read(128 * 1024), handle.identity()
                elif path in proposed:
                    old = proposed[path].encode('utf-8')
                    identity = 'after-prepare'  # Real identity captured before integration.
                merged = desktop_integration.merge_content(path, old, content)
                sanitize(merged)
                edits.append(dict(schema_version=1, owner='harness-desktop-v1', path=path, content=merged, old_hash=sha(old) if old is not None else None,
                    old_identity=identity, new_hash=sha(merged.encode()), backup=f'{len(edits):02d}.bak' if old is not None else None))
            desktop_integration.authorized(edits, policy)
        except ConfigError as error:
            blockers.append(error.code)
        value = dict(schema_version=1, kind='guided_onboarding_plan', run_id=uuid.uuid4().hex, request=request.model_dump(), provenance=draft.model_dump(),
            target_identity=tree.base.identity(), init_v1=initial.model_dump(), preparation=preparation.model_dump(),
            integration_edits=edits, desktop_resource_sha256=desktop_digest(), guided_resource_sha256=guided_resources.resource_digest(),
            development_policy_sha256=development_hash, blockers=sorted(set(blockers)))
        plan = GuidedOnboardingPlan.model_validate(dict(value, plan_sha256=sha(canonical(value))))
    if plan_out is not None: export(plan_out, plan.model_dump(), [*external_paths(plan), str(local)])
    return dict(schema_version=1, command='onboard', status='blocked' if blockers else 'ready', checks=base['checks'],
        questions=[], fields=collected['fields'], discovered_facts=facts, plan=plan.model_dump(), applicable=not blockers,
        integration_plan_path=str(integration_file(plan)), prepared=False, certified=False,
        supervised_preparation_accepted=False, remote_not_checked=True), (1 if blockers else 0)


def folder(plan): return safe_path(Path(plan.preparation.binding.state_dir) / ('guided-' + plan.run_id))


def integration_file(plan):
    # 02 explicitly requires its immutable input plan outside checkout/state.
    return Path(plan.request.binding_path).with_name('guided-' + plan.run_id + '-integration.json')


def selected(plan_path):
    plan_path = unmanaged_path(str(safe_path(plan_path)))
    plan = load_json(plan_path, GuidedOnboardingPlan)
    separate([str(plan_path), *external_paths(plan), tool_path(plan.preparation)])
    if plan.guided_resource_sha256 != guided_resources.resource_digest() or plan.desktop_resource_sha256 != desktop_digest():
        raise ConfigError('guided_resource_drift')
    if plan.blockers or not plan.preparation.applicable: raise ConfigError('plan_not_applicable')
    if digest(plan.request.policy_path) != plan.preparation.policy_sha256: raise ConfigError('stale_plan')
    if plan.request.development_policy_path and digest(plan.request.development_policy_path) != plan.development_policy_sha256:
        raise ConfigError('stale_plan')
    from .diagnostics import checkout
    target, origin = checkout(plan.request.target_path)
    if origin != plan.preparation.origin: raise ConfigError('stale_plan')
    with PinnedTree(target) as tree:
        if tree.base.identity() != plan.target_identity: raise ConfigError('plan_identity_mismatch')
    # Prove all frozen derived payloads. Hash alone is not an authorization.
    resolved = collect(plan.provenance)
    if resolved['questions'] or parse(GuidedRequest, dict(schema_version=1, **resolved['values'])) != plan.request:
        raise ConfigError('invalid_guided_plan')
    p = plan.preparation
    if any(getattr(p,k) != getattr(plan.init_v1,k) for k in ('binding','descriptor','target_path','origin','policy_path','policy_sha256','binding_path','binding_mode','resource_manifest_sha256')):
        raise ConfigError('invalid_guided_plan')
    content = application.content_map(plan.init_v1)
    content.update({'.harness/development.yaml': serialized(plan.request.development.model_dump()),
        '.harness/context.md': context_content(plan.request.development),
        '.agents/skills/harness-client-onboarding/SKILL.md': guided_resources.resources()['harness-client-onboarding/SKILL.md']})
    binding_content = serialized(p.binding.model_dump())
    for op in p.operations:
        expected = content.get(op.path) if op.scope == 'target' else (
            binding_content if op.path == p.binding_path else serialized(plan.request.tool_binding.model_dump()) if op.path == tool_path(p) else None)
        if expected != op.content: raise ConfigError('invalid_guided_plan')
    if authorize(p.operations, load_document(p.policy_path, Policy)): raise ConfigError('plan_not_applicable')
    return plan


def load_run(plan):
    run = load_json(folder(plan) / 'journal.json', OnboardingRun)
    if (run.client_id, run.checkout_id, run.run_id, run.plan_sha256, run.target_identity) != (
        plan.preparation.binding.client_id, plan.preparation.binding.checkout_id, plan.run_id, plan.plan_sha256, plan.target_identity):
        raise ConfigError('foreign_journal')
    if [s.name for s in run.stages] != ['preflight','collect','preview','prepare','integrate','certify']: raise ConfigError('invalid_journal')
    allowed = {(o.scope, o.path): o for o in plan.preparation.operations}
    keys = []
    for op in run.operations:
        key = (op.scope, op.kind, op.path.lower())
        if key in keys: raise ConfigError('invalid_journal')
        keys.append(key)
        if op.kind == 'file':
            expected = allowed.get((op.scope, op.path))
            if not expected or expected.sha256 != op.sha256: raise ConfigError('invalid_journal')
        elif op.scope != 'target' or not any(o.scope == 'target' and o.path.startswith(op.path + '/') for o in plan.preparation.operations):
            raise ConfigError('invalid_journal')
    if {(o.scope,o.path) for o in run.operations if o.kind == 'file'} != set(allowed): raise ConfigError('invalid_journal')
    return run


def stage_record(run, name): return next(s for s in run.stages if s.name == name)


def response(plan, run, *, blocked=False, **extra):
    stages = {s.name:s.status for s in run.stages}
    prepared = stages['prepare'] == 'completed'
    result = dict(schema_version=1, command='onboard', status='blocked' if blocked else 'partial', checks=[],
        client_id=run.client_id, checkout_id=run.checkout_id, run_id=run.run_id, plan_sha256=run.plan_sha256,
        stages=stages, prepared=prepared, certified=False, supervised_preparation_accepted=False, remote_not_checked=True,
        limitations=[], blocked_required=[],
        recovery_required=any(v in ('in_progress','failed','conflict') for v in stages.values()), **extra)
    evidence_path = folder(plan)/'certification.json'
    if evidence_path.exists():
        from harness_core.guided import CertificationInput
        from harness_core.desktop import assess_certificate
        from harness_core.supervised import assess_preparation
        evidence = load_json(evidence_path,CertificationInput)
        if (evidence.snapshot.client_id,evidence.snapshot.checkout_id) != (run.client_id,run.checkout_id):
            raise ConfigError('supervised_identity_mismatch')
        strict = assess_certificate(plan.request.catalog,evidence.certificate)
        result.update(strict_certificate=strict,limitations=[c['id'] for c in strict['checks'] if c['status']!='observed'])
        if stages['certify'] in ('completed','blocked') and stages['integrate']=='completed':
            assessment = assess_preparation(plan.request.catalog,evidence.certificate,evidence.snapshot,evidence.acceptance,
                required=evidence.required_capabilities)
            comparison = supervised.compare(plan.request.target_path,plan.request.policy_path,plan.request.binding_path,
                evidence.snapshot,evidence.certificate)
            accepted = assessment['prepared'] and comparison['intact'] and stages['certify']=='completed'
            result.update(certified=bool(strict['certified'] and accepted),supervised_preparation_accepted=bool(accepted),
                blocked_required=assessment['blocked_required'],candidate_comparison=comparison)
            if stages['certify']=='completed' and not accepted: blocked=True; result['status']='blocked'
    return result, (1 if blocked else 0)


def operation_path(plan, entry):
    if entry.scope == 'target': return Path(plan.request.target_path), entry.path
    return Path(entry.path).parent, Path(entry.path).name


def verify_prepared(plan, run, *, integrated=False):
    """All creations and all preserved inputs remain exactly as reviewed."""
    integration = {e.path:e.new_hash for e in plan.integration_edits} if integrated else {}
    for entry in run.operations:
        root, relative = operation_path(plan, entry)
        with PinnedTree(root) as tree:
            with (tree.directory if entry.kind == 'directory' else tree.file)(relative) as handle:
                if entry.state != 'created' or handle.identity() != entry.file_identity: raise ConfigError('application_conflict')
                expected = integration.get(entry.path, entry.sha256) if entry.scope == 'target' else entry.sha256
                if entry.kind == 'file' and sha(handle.read(128 * 1024)) != expected: raise ConfigError('application_conflict')
    for name, expected in plan.preparation.input_hashes.items():
        if name == 'policy': path = Path(plan.request.policy_path)
        elif name == 'binding':
            if plan.preparation.binding_mode == 'proposed': continue
            path = Path(plan.request.binding_path)
        elif name == 'tools': path = Path(tool_path(plan.preparation))
        else:
            relative = '.harness/client.yaml' if name == 'descriptor' else name
            path = Path(plan.request.target_path) / relative
            expected = integration.get(relative, expected)
        if digest(path) != expected: raise ConfigError('application_conflict')


def regenerate(plan, probe_fn):
    current, _ = preview(plan.provenance, probe_fn=probe_fn)
    rebuilt = current['plan']
    frozen = plan.model_dump()
    for field in ('run_id', 'plan_sha256'): rebuilt.pop(field); frozen.pop(field)
    if rebuilt != frozen: raise ConfigError('stale_plan')


def new_run(plan):
    state = ensure_state(plan.preparation.binding)
    # All effects are after preflight. Shared checkout lock serializes v1/02/03.
    with PinnedTree(state) as tree:
        with tree.directory('guided-' + plan.run_id, create=True): pass
    run = OnboardingRun(schema_version=1, client_id=plan.preparation.binding.client_id, checkout_id=plan.preparation.binding.checkout_id,
        run_id=plan.run_id, plan_sha256=plan.plan_sha256, target_identity=plan.target_identity,
        stages=[StageRecord(schema_version=1,name=n,status='completed' if n in ('preflight','collect','preview') else 'not_run')
            for n in ('preflight','collect','preview','prepare','integrate','certify')], operations=[])
    directories = set()
    for op in plan.preparation.operations:
        if op.scope == 'target':
            for parent in Path(op.path).parents:
                if str(parent) != '.' and not safe_path(Path(plan.request.target_path) / parent).exists(): directories.add(parent.as_posix())
    run.operations = [OperationRecord(schema_version=1, scope='target', kind='directory', path=d, state='planned')
        for d in sorted(directories, key=lambda d:(d.count('/'), d))]
    run.operations.extend(OperationRecord(schema_version=1, scope=o.scope, kind='file', path=o.path, state='planned', sha256=o.sha256)
        for o in plan.preparation.operations)
    persist(folder(plan) / 'journal.json', run)
    export(folder(plan) / 'plan.json', plan.model_dump(), [plan.request.target_path, plan.request.policy_path, plan.request.binding_path])
    return run


def apply(plan_path, *, stage, evidence=None, probe_fn=probe):
    if stage not in ('prepare','integrate','certify'): raise ConfigError('invalid_guided_stage')
    if (stage == 'certify') != (evidence is not None): raise ConfigError('invalid_arguments')
    plan = selected(plan_path)
    with ExitStack() as stack:
        target_tree = stack.enter_context(PinnedTree(plan.request.target_path))
        for input_path in (plan_path, plan.request.policy_path, *([plan.request.development_policy_path] if plan.request.development_policy_path else [])):
            p = safe_path(input_path); tree = stack.enter_context(PinnedTree(p.parent)); stack.enter_context(tree.file(p.name))
        if target_tree.base.identity() != plan.target_identity: raise ConfigError('plan_identity_mismatch')
        if not folder(plan).exists():
            if stage != 'prepare': raise ConfigError('guided_prepare_required')
            regenerate(plan, probe_fn)
            # Freeze preserved target inputs and existing external bindings until all writes finish.
            for name in plan.preparation.input_hashes:
                if name == 'policy' or (name == 'binding' and plan.preparation.binding_mode == 'proposed'): continue
                p = (Path(plan.request.binding_path) if name == 'binding' else Path(tool_path(plan.preparation)) if name == 'tools' else
                    Path(plan.request.target_path) / ('.harness/client.yaml' if name == 'descriptor' else name))
                tree = stack.enter_context(PinnedTree(p.parent)); stack.enter_context(tree.file(p.name))
            # Check incomplete prior 03 runs, never silently resume them.
            state = safe_path(plan.preparation.binding.state_dir)
            if state.exists():
                for journal in state.glob('guided-*/journal.json'):
                    other = load_json(journal, OnboardingRun)
                    if (other.client_id,other.checkout_id) != (plan.preparation.binding.client_id,plan.preparation.binding.checkout_id): raise ConfigError('foreign_journal')
                    if any(s.status in ('failed','in_progress','conflict') for s in other.stages): raise ConfigError('recovery_required')
            state = ensure_state(plan.preparation.binding)
            with CheckoutLock(state, plan.run_id):
                regenerate(plan, probe_fn)
                run = new_run(plan)
                with CheckoutLock(folder(plan), plan.run_id):
                    return prepare_stage(plan, run)
        stack.enter_context(CheckoutLock(folder(plan), plan.run_id))
        run = load_run(plan)
        record = stage_record(run, stage)
        if stage == 'prepare':
            if record.status != 'completed': raise ConfigError('recovery_required')
            verify_prepared(plan, run, integrated=stage_record(run,'integrate').status == 'completed')
            return response(plan, run, idempotent=True)
        if stage_record(run,'prepare').status != 'completed': raise ConfigError('guided_prepare_required')
        if stage == 'integrate': return integrate_stage(plan, run)
        return certify_stage(plan, run, evidence)


def prepare_stage(plan, run):
    path = folder(plan) / 'journal.json'
    record = stage_record(run, 'prepare'); record.status = 'in_progress'; persist(path, run)
    try:
        with ExitStack() as stack:
            trees = {'target':stack.enter_context(PinnedTree(plan.request.target_path)),
                     'binding':stack.enter_context(PinnedTree(Path(plan.request.binding_path).parent))}
            for entry in run.operations:
                if entry.scope == 'binding' and entry.path == plan.request.binding_path: checkpoint('before_binding')
                root, relative = operation_path(plan, entry)
                entry.state = 'creating'; persist(path, run)
                tree = trees[entry.scope]
                opener = tree.directory if entry.kind == 'directory' else tree.file
                with opener(relative, create=True) as handle:
                    if entry.kind == 'file':
                        operation = next(o for o in plan.preparation.operations if o.scope == entry.scope and o.path == entry.path)
                        handle.write(operation.content.encode('utf-8'))
                    entry.file_identity = handle.identity(); entry.state = 'created'; persist(path, run)
                if entry.scope == 'binding' and entry.path == plan.request.binding_path: checkpoint('after_binding')
        record.status = 'completed'; persist(path, run)
        return response(plan, run)
    except (ConfigError, OSError) as error:
        # A failed journal persistence must not upgrade intent to ownership.
        run = load_run(plan); record = stage_record(run,'prepare'); record.status = 'failed'
        record.error_code = error.code if isinstance(error,ConfigError) else 'application_failed'
        persist(path, run)
        return response(plan, run, blocked=True)


def actual_integration(plan, run):
    integration_path = integration_file(plan)
    from harness_core.desktop import DesktopIntegrationPlan
    actual = load_json(integration_path, DesktopIntegrationPlan)
    if actual.plan_sha256 != run.integration_plan_sha256 or actual.catalog != plan.request.catalog:
        raise ConfigError('invalid_guided_plan')
    if actual.target_path != plan.preparation.target_path or actual.binding != plan.preparation.binding:
        raise ConfigError('invalid_guided_plan')
    expected = [{k:v for k,v in e.model_dump().items() if k not in ('old_identity','backup')} for e in plan.integration_edits]
    observed = [{k:v for k,v in e.model_dump().items() if k not in ('old_identity','backup')} for e in actual.edits]
    if observed != expected: raise ConfigError('integration_drift')
    if any(expected.old_identity not in (None,'after-prepare') and expected.old_identity != observed.old_identity
        for expected,observed in zip(plan.integration_edits,actual.edits,strict=True)):
        raise ConfigError('integration_drift')
    return integration_path, actual


def integrate_stage(plan, run):
    path = folder(plan) / 'journal.json'; record = stage_record(run, 'integrate')
    if record.status == 'completed':
        integration_path, actual = actual_integration(plan, run)
        verify_prepared(plan, run, integrated=True)
        # The independent 02 recovery preview verifies all owned integration records.
        check, code = desktop_integration.recover(plan.request.target_path, plan.request.policy_path, integration_path)
        if code: raise ConfigError('integration_drift')
        return response(plan, run, idempotent=True)
    if record.status not in ('not_run', 'recovered'): raise ConfigError('recovery_required')
    verify_prepared(plan, run)
    result, _ = desktop_integration.preview(plan.request.target_path, plan.request.policy_path, plan.request.binding_path, plan.request.catalog)
    # Compare every proposed byte and precondition against the reviewed composite preview.
    from harness_core.desktop import DesktopIntegrationPlan
    actual = DesktopIntegrationPlan.model_validate(result['plan'])
    expected = [{k:v for k,v in e.model_dump().items() if k not in ('old_identity','backup')} for e in plan.integration_edits]
    observed = [{k:v for k,v in e.model_dump().items() if k not in ('old_identity','backup')} for e in actual.edits]
    if observed != expected: raise ConfigError('integration_drift')
    if any(expected.old_identity not in (None,'after-prepare') and expected.old_identity != observed.old_identity
        for expected,observed in zip(plan.integration_edits,actual.edits,strict=True)):
        raise ConfigError('integration_drift')
    integration_path = integration_file(plan)
    # Do not replace an old plan on retries; recovered runs require a new preview.
    if integration_path.exists(): raise ConfigError('guided_new_preview_required')
    export(integration_path, actual.model_dump(), external_paths(plan))
    run.integration_plan_sha256 = actual.plan_sha256
    record.status = 'in_progress'; persist(path, run)
    try:
        checkpoint('integration')
        result, code = desktop_integration.apply(plan.request.target_path, plan.request.policy_path, integration_path)
        record.status = 'failed' if code else 'completed'
        record.error_code = 'integration_failed' if code else None
        persist(path, run)
        return response(plan, run, blocked=bool(code))
    except (ConfigError, OSError) as error:
        record.status = 'failed'; record.error_code = error.code if isinstance(error, ConfigError) else 'integration_failed'
        persist(path, run)
        return response(plan, run, blocked=True)


def certify_stage(plan, run, evidence):
    if stage_record(run, 'integrate').status != 'completed': raise ConfigError('integration_not_applied')
    verify_prepared(plan, run, integrated=True)
    integration_path, actual = actual_integration(plan, run)
    if (evidence.snapshot.client_id,evidence.snapshot.checkout_id) != (run.client_id,run.checkout_id): raise ConfigError('supervised_identity_mismatch')
    result = supervised.prepare(plan.request.target_path, plan.request.policy_path, plan.request.binding_path, integration_path,
        plan.request.catalog, evidence.certificate, evidence.snapshot, evidence.acceptance, required=evidence.required_capabilities)
    record = stage_record(run, 'certify'); record.status = 'completed' if result['prepared'] else 'blocked'
    record.error_code = None if result['prepared'] else 'certification_blocked'
    persist(folder(plan) / 'certification.json', evidence)
    persist(folder(plan) / 'journal.json', run)
    report, code = response(plan, run, blocked=not result['prepared'])
    report.update(certified=bool(result['certified'] and result['prepared']), supervised_preparation_accepted=result['prepared'], limitations=result['limitations'],
        blocked_required=result['blocked_required'], checks=result['checks'], strict_certificate=result['strict_certificate'],
        candidate_comparison=result['candidate_comparison'])
    return report, code


def recover(plan_path, *, stage, apply_changes=False):
    if stage not in ('prepare','integrate'): raise ConfigError('invalid_guided_stage')
    plan = selected(plan_path)
    with ExitStack() as stack:
        stack.enter_context(PinnedTree(plan.request.target_path))
        for input_path in (plan_path,plan.request.policy_path):
            p=safe_path(input_path); tree=stack.enter_context(PinnedTree(p.parent)); stack.enter_context(tree.file(p.name))
        stack.enter_context(CheckoutLock(folder(plan),plan.run_id,recover=apply_changes))
        selected(plan_path)
        return _recover(plan,stage=stage,apply_changes=apply_changes)


def _recover(plan, *, stage, apply_changes):
    run = load_run(plan)
    if stage == 'integrate':
        path, actual = actual_integration(plan, run)
        if not (desktop_integration.run_folder(actual) / 'journal.json').exists():
            # Preflight failed before 02 created any journal; no integration effects.
            rendered, _ = desktop_integration.preview(plan.request.target_path,plan.request.policy_path,plan.request.binding_path,plan.request.catalog)
            if [{k:v for k,v in e.items() if k not in ('old_identity','backup')} for e in rendered['plan']['edits']] != [{k:v for k,v in e.model_dump().items() if k not in ('old_identity','backup')} for e in actual.edits]:
                raise ConfigError('integration_drift')
            result, code = dict(recovery_status='recovered' if apply_changes else 'preview'), 0
        else:
            result, code = desktop_integration.recover(plan.request.target_path,plan.request.policy_path,path,apply_changes=apply_changes)
            if apply_changes and not code:
                # 02 deliberately retains empty directories. The composite owns
                # parent directories too: retire only proven, empty child dirs.
                from harness_core.desktop import IntegrationJournal
                journal_path=desktop_integration.run_folder(actual)/'journal.json'
                with CheckoutLock(plan.preparation.binding.state_dir,plan.run_id,recover=True):
                    journal=load_json(journal_path,IntegrationJournal)
                    if journal.plan_sha256!=actual.plan_sha256 or journal.target_identity!=plan.target_identity or journal.state!='recovered':
                        raise ConfigError('integration_drift')
                    retained,conflicts=[],[]
                    with PinnedTree(plan.request.target_path) as tree:
                        for record in sorted((r for r in journal.records if r.kind=='directory'),key=lambda r:r.path.count('/'),reverse=True):
                            if not any(e.path.startswith(record.path+'/') for e in actual.edits): raise ConfigError('invalid_journal')
                            if record.state=='recovered': continue
                            selected_path=safe_path(Path(plan.request.target_path)/record.path)
                            if not selected_path.exists(): record.state='recovered'; continue
                            try:
                                with tree.directory(record.path,delete=True) as handle:
                                    if handle.identity()!=record.identity: raise ConfigError('recovery_conflict')
                                    if any(selected_path.iterdir()): retained.append(record.path); continue
                                    handle.delete(); record.state='recovered'
                            except (ConfigError,OSError): conflicts.append(record.path)
                    persist(journal_path,journal)
                    result.update(retained_directories=retained,conflicts=conflicts)
                    if conflicts: code=1
        if apply_changes:
            stage_record(run,'integrate').status = 'conflict' if code else 'recovered'
            stage_record(run,'certify').status = 'not_run'; persist(folder(plan)/'journal.json',run)
        report, _ = response(plan, run, blocked=bool(code))
        report['recovery_status'] = ('conflict' if code else result.get('recovery_status','recovered')) if apply_changes else 'preview'
        report['conflicts'] = result.get('conflicts',[])
        report['retained_directories'] = result.get('retained_directories',[])
        return report, code
    if stage_record(run,'integrate').status not in ('not_run','recovered'): raise ConfigError('guided_recover_integration_first')
    actions, conflict = [], False
    with ExitStack() as stack:
        stack.enter_context(PinnedTree(plan.request.target_path))
        if apply_changes: stack.enter_context(CheckoutLock(plan.preparation.binding.state_dir,plan.run_id,recover=True))
        for entry in reversed(run.operations):
            root, relative = operation_path(plan, entry)
            actual = safe_path(root / relative); status = 'removed'
            try:
                if entry.state in ('planned','removed'):
                    if entry.state == 'planned' and actual.exists(): raise ConfigError('recovery_conflict')
                elif actual.exists():
                    if not entry.file_identity or entry.state not in ('created','conflict'): raise ConfigError('recovery_conflict')
                    with PinnedTree(root) as tree:
                        opener = tree.directory if entry.kind == 'directory' else tree.file
                        with opener(relative, delete=apply_changes) as handle:
                            if handle.identity() != entry.file_identity: raise ConfigError('recovery_conflict')
                            if entry.kind == 'file' and sha(handle.read(128 * 1024)) != entry.sha256: raise ConfigError('recovery_conflict')
                            if entry.kind == 'directory' and any(actual.iterdir()):
                                removable = {a['path'] for a in actions if a['status'] == 'removed' and a['scope'] == 'target'}
                                if apply_changes or any(p.relative_to(root).as_posix() not in removable for p in actual.iterdir()): raise ConfigError('recovery_conflict')
                            if apply_changes: handle.delete()
            except (ConfigError, OSError): status, conflict = 'conflict', True
            actions.append(dict(path=entry.path,scope=entry.scope,status=status,
                reason='Propiedad o contenido en conflicto; conservar archivo.' if status=='conflict' else 'Recurso propio revisado para recuperación.'))
            if apply_changes: entry.state = status; persist(folder(plan)/'journal.json',run)
        if apply_changes:
            stage_record(run,'prepare').status = 'conflict' if conflict else 'recovered'
            persist(folder(plan)/'journal.json',run)
    report, code = response(plan, run, blocked=conflict)
    report.update(recovery_status=('conflict' if conflict else 'recovered') if apply_changes else 'preview', actions=actions)
    return report, code
