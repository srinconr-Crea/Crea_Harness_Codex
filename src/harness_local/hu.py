"""Transactional local HU adapters. Never execute client code or publish remotely."""
from contextlib import contextmanager,nullcontext
from functools import wraps
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import uuid

from pydantic import ValidationError, TypeAdapter

from harness_core.configuration import ConfigError, safe_path, digest
from harness_core.contracts import ID
from harness_core.guided import sanitize, GuidedOnboardingPlan
from harness_core.hu import (INPUTS, HuRun, PlanRevision, ApprovalRecord, Candidate,
    GateResult, WorktreeRecord, covers, approval_current, evidence_gate)
from harness_core.onboarding_plan import canonical, sha, denied, separate, unmanaged_path, load_json
from .desktop_integration import selected, input_hashes
from .desktop_resources import resource_digest
from .quality_resources import load_quality
from .execution_state import ensure_state, CheckoutLock, persist
from .windows_fs import PinnedTree
from .diagnostics import git_read, local_status


def checkpoint(point):
    """Fault-injection seam. Production has no effect."""


def parse(model, value):
    sanitize(value)
    try:
        return model.model_validate(value)
    except (ValidationError, TypeError):
        raise ConfigError('invalid_hu_document') from None


def now():
    return datetime.now(timezone.utc).isoformat()


def git_names(target, *args):
    # ls-tree/ls-files never run filters, diff drivers, textconv, hooks or client code.
    # NUL framing preserves leading/trailing spaces in filenames. git_read strips
    # scalar output, which is appropriate for HEAD but not for path inventories.
    import shutil
    from .diagnostics import run_bounded
    from .tool_runtime import executable as selected_executable
    executable=selected_executable('git')
    if not executable: raise ConfigError('tool_missing')
    env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull)
    for key in ('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE','GIT_COMMON_DIR'): env.pop(key,None)
    text=run_bounded([executable,'-c','core.fsmonitor=false','-C',str(target),*args],env=env)
    return text.split('\0') if text else []


def scope_read(access, policy, path, paths):
    if access is None: return
    from harness_core.setup import authorize_access
    from harness_core.setup import within
    if within(path,access.inputs.access_scope.deny) or denied(path,policy.denied_paths):
        raise ConfigError('hu_access_denied')
    if path in access.technical_reads or path in access.integration_writes:
        return  # Exact managed paths were declared in the reviewed setup plan.
    try: authorize_access(access.inputs.access_scope,policy,path,'read',paths)
    except ConfigError: raise ConfigError('hu_access_denied') from None


def scope_write(access, policy, path, paths):
    if access is None: return
    from harness_core.setup import authorize_access
    try: authorize_access(access.inputs.access_scope,policy,path,'write',paths,read_required=True)
    except ConfigError: raise ConfigError('hu_access_denied') from None


def baseline(target, access=None, policy=None):
    status = local_status(target)
    if status.status != 'ready' or status.code != 'clean': raise ConfigError('hu_clean_base_required')
    values, total = {}, 0
    with PinnedTree(target) as tree:
        names = [p for p in git_names(target,'ls-files','-z','--cached') if p]
        if len(names)>4096: raise ConfigError('hu_candidate_too_large')
        for name in names:
            scope_read(access,policy,name,access.inputs.access_scope.read_allow if access else [])
            with tree.file(name) as handle: raw=handle.read(2*1024*1024)
            total+=len(raw)
            if total>16*1024*1024: raise ConfigError('hu_candidate_too_large')
            values[name]=sha(raw)
    return values


def capture(target, run, policy, access=None):
    try:
        before = capture_once(target,run,policy,access)
        after = capture_once(target,run,policy,access)
    except ConfigError as error:
        if error.code=='document_too_large': raise ConfigError('hu_candidate_too_large') from None
        raise
    if before != after: raise ConfigError('hu_candidate_changed_during_capture')
    return after


def capture_once(target, run, policy, access=None):
    base = git_read(target, 'rev-parse', 'HEAD')
    if base != run.base: raise ConfigError('hu_base_changed')
    tracked = {}
    base_modes = {}
    for line in git_names(target, 'ls-tree', '-r', '-z', run.base):
        if not line: continue
        info, path = line.split('\t', 1)
        mode, kind, oid = info.split()
        if mode not in ('100644', '100755') or kind != 'blob': raise ConfigError('hu_unsupported_entry')
        tracked[path] = oid
        base_modes[path] = mode
    indexed = {}
    for line in git_names(target,'ls-files','--stage','-z'):
        if not line: continue
        info,path=line.split('\t',1)
        mode,oid,stage=info.split()
        if stage!='0' or mode not in ('100644','100755'): raise ConfigError('hu_unsupported_entry')
        indexed[path]=(mode,oid)
    names = set(tracked)
    names.update(p for p in git_names(target, 'ls-files', '-z', '--cached', '--others', '--exclude-standard') if p)
    # Include explicitly selected ignored files; directories are traversed without following links.
    for scope in run.plan.paths:
        scope_write(access,policy,scope.rstrip('/')+('/scope-check' if scope.endswith('/') else ''),run.plan.paths)
        p = safe_path(target / scope)
        if p.is_file(): names.add(scope.rstrip('/'))
        elif p.is_dir():
            for child in p.rglob('*'):
                child = safe_path(child)
                if child.is_file(): names.add(child.relative_to(target).as_posix())
    if len(names) > 4096: raise ConfigError('hu_candidate_too_large')
    entries, total = [], 0
    with PinnedTree(target) as tree:
        for path in sorted(names):
            from harness_core.onboarding_plan import destination_path
            destination_path(path)
            # Unknown external files are rejected before contents are read.
            scope_read(access,policy,path,access.inputs.access_scope.read_allow if access else [])
            if path not in run.baseline_files:
                scope_write(access,policy,path,run.plan.paths)
            p = safe_path(target / path)
            before = tracked.get(path)
            index_mode,index_oid=indexed.get(path,(None,None))
            staged_operation = None
            if (index_mode,index_oid) != (base_modes.get(path),before):
                staged_operation='delete' if index_oid is None else ('modify' if before else 'create')
            content = None
            if p.exists():
                if not p.is_file(): raise ConfigError('hu_unsupported_entry')
                with tree.file(path) as handle: raw = handle.read(2 * 1024 * 1024)
                content = sha(raw)
                if content == run.baseline_files.get(path) and staged_operation is None: continue
                total += len(raw)
                if total > 16 * 1024 * 1024: raise ConfigError('hu_candidate_too_large')
            elif before is None and staged_operation is None: continue
            scope_write(access,policy,path,run.plan.paths)
            operation = 'delete' if content is None else ('modify' if before else 'create')
            if (not covers(path, run.plan.paths) or operation not in run.plan.operations or
                (staged_operation is not None and staged_operation not in run.plan.operations) or
                denied(path, ['.git/', '.harness/', '.codex/', '.agents/'] + policy.denied_paths + policy.read_only_paths)):
                raise ConfigError('hu_scope_denied')
            entries.append(dict(schema_version=1, path=path, operation=operation, base_oid=before, content_sha256=content,
                index_oid=index_oid,index_mode=index_mode,staged_operation=staged_operation))
    if len(entries) > policy.max_files or total > policy.max_bytes: raise ConfigError('hu_candidate_too_large')
    value = dict(schema_version=1, base=run.base, baseline_sha256=sha(canonical(run.baseline_files)), context_sha256=run.context_sha256,
        plan_sha256=run.plan.plan_sha256, entries=entries)
    return parse(Candidate, {**value, 'candidate_sha256':sha(canonical(value))})


def with_hu_tools(function):
    @wraps(function)
    def call(self,*args,**kwargs):
        from .tool_runtime import using_tools
        tools=self.selected_tools()
        with using_tools(tools) if tools else nullcontext(): return function(self,*args,**kwargs)
    return call


class HuService:
    def __init__(self, target, policy, binding):
        self.policy_path, self.binding_path = safe_path(policy), safe_path(binding)
        self.access_path=self.binding_path.with_name(self.binding_path.name+'.setup.json')
        from .tool_runtime import using_tools
        tools=self.selected_tools()
        with using_tools(tools) if tools else nullcontext(): self.target, self.config = selected(target, policy, binding)
        self.state = safe_path(self.config['binding'].state_dir)
        self.access=self.load_access()

    def selected_tools(self):
        from harness_core.setup import SetupPlan,InstallationRecord,InstalledTool
        if not safe_path(self.access_path).exists(): return None
        access=load_json(self.access_path,SetupPlan)
        raw=json.loads(access.child_payloads['tools']) if 'tools' in access.child_payloads else None
        if raw is None: return None
        tools={t['name']:InstalledTool.model_validate(t) for t in raw['existing']}
        if access.inputs.installation_record:
            record=load_json(access.inputs.installation_record,InstallationRecord,limit=8*1024*1024)
            tools.update({t.name:t for t in record.tools})
        return list(tools.values())

    def load_access(self):
        from harness_core.setup import SetupPlan
        if not safe_path(self.access_path).exists(): return None
        access=load_json(self.access_path,SetupPlan)
        b=self.config['binding']
        if access.inputs.binding!=b or access.inputs.policy!=self.config['policy']:
            raise ConfigError('hu_identity_mismatch')
        if access.inputs.access_scope.policy_sha256!=digest(self.policy_path):
            raise ConfigError('hu_identity_mismatch')
        return access

    def context_hash(self):
        hashes = input_hashes(self.target, self.policy_path, self.binding_path)
        for relative in ('.harness/development.yaml', '.harness/context.md'):
            hashes[relative] = digest(self.target / relative)
        hashes['tools'] = digest(self.binding_path.with_name(self.binding_path.name+'.tools.json'))
        hashes['desktop_kit'] = resource_digest()
        hashes['practices'] = sha(canonical(load_quality().practices.model_dump()))
        if self.access is not None: hashes['access_scope']=sha(canonical(self.access.model_dump()))
        if self.access and self.access.inputs.installation_record:
            path=safe_path(self.access.inputs.installation_record)
            with PinnedTree(path.parent) as tree:
                with tree.file(path.name) as handle: hashes['installation']=sha(handle.read(8*1024*1024))
        return sha(canonical(hashes))

    def prepared(self, path):
        from . import guided_onboarding as guided
        # Consume a completed receipt, never replay a 03 write plan. Its frozen
        # kit can precede the current passive HU procedure; v1 selected/apply keeps
        # its exact-version check. Verify actual owned files against its journal.
        try: plan = load_json(path,GuidedOnboardingPlan)
        except OSError: raise ConfigError('hu_preparation_required') from None
        b = self.config['binding']
        if (plan.preparation.binding.client_id, plan.preparation.binding.checkout_id,
            safe_path(plan.request.target_path), safe_path(plan.request.binding_path), safe_path(plan.request.policy_path)) != (
            b.client_id, b.checkout_id, self.target, self.binding_path, self.policy_path):
            raise ConfigError('hu_identity_mismatch')
        run = guided.load_run(plan)
        if plan.blockers or not plan.preparation.applicable: raise ConfigError('hu_preparation_required')
        with PinnedTree(self.target) as tree:
            if tree.base.identity()!=plan.target_identity: raise ConfigError('hu_identity_mismatch')
        if next(s.status for s in run.stages if s.name == 'prepare') != 'completed':
            raise ConfigError('hu_preparation_required')
        guided.verify_prepared(plan, run, integrated=next(s.status for s in run.stages if s.name == 'integrate') == 'completed')
        return plan

    @contextmanager
    def database(self, create=False, readonly=False):
        if create: ensure_state(self.config['binding'])
        if not self.state.exists(): raise ConfigError('hu_not_found')
        with PinnedTree(self.state):
            for name in ('hu.sqlite3', 'hu.sqlite3-journal', 'hu.sqlite3-wal', 'hu.sqlite3-shm'):
                p = safe_path(self.state / name)
                if p.exists() and (not p.is_file() or p.stat().st_nlink != 1): raise ConfigError('hu_state_conflict')
            db_path = self.state / 'hu.sqlite3'
            if not create and not db_path.exists(): raise ConfigError('hu_not_found')
            with nullcontext() if readonly else CheckoutLock(self.state, 'hu', recover=True):
                db = sqlite3.connect(db_path.as_uri()+'?mode=ro',uri=True,timeout=1,isolation_level=None) if readonly else sqlite3.connect(db_path, timeout=1, isolation_level=None)
                try:
                    if not readonly: db.execute('PRAGMA synchronous=FULL')
                    version = db.execute('PRAGMA user_version').fetchone()[0]
                    if version not in (0, 1): raise ConfigError('hu_state_version')
                    if readonly and version!=1: raise ConfigError('hu_state_version')
                    if not readonly: db.execute('BEGIN IMMEDIATE')
                    if version == 0:
                        if db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]:
                            raise ConfigError('hu_state_version')
                        db.execute('CREATE TABLE runs (story TEXT PRIMARY KEY, payload TEXT NOT NULL)')
                        db.execute('CREATE TABLE events (seq INTEGER PRIMARY KEY, story TEXT NOT NULL, operation TEXT NOT NULL, request_hash TEXT NOT NULL, payload TEXT NOT NULL, UNIQUE(story, operation))')
                        db.execute('CREATE TABLE pending (story TEXT PRIMARY KEY, payload TEXT NOT NULL)')
                        db.execute('PRAGMA user_version=1')
                    yield db
                    if db.in_transaction: db.commit()
                except sqlite3.Error:
                    if db.in_transaction: db.rollback()
                    raise ConfigError('hu_state_conflict') from None
                except BaseException:
                    if db.in_transaction: db.rollback()
                    raise
                finally: db.close()

    def load(self, db, story):
        row = db.execute('SELECT payload FROM runs WHERE story=?', (story,)).fetchone()
        if not row: raise ConfigError('hu_not_found')
        run = parse(HuRun, json.loads(row[0]))
        b = self.config['binding']
        with PinnedTree(self.target) as tree:
            if (run.client_id, run.checkout_id, run.target_identity) != (b.client_id, b.checkout_id, tree.base.identity()):
                raise ConfigError('hu_identity_mismatch')
        return run

    def history(self, db, story):
        return [json.loads(row[0]) for row in db.execute('SELECT payload FROM events WHERE story=? ORDER BY seq', (story,))]

    def response(self, run, status='ready', gate=None, **extra):
        return dict(schema_version=1, command='hu', status=status, checks=[gate.model_dump()] if gate else [],
            run=run.model_dump(), publication_allowed=False, certified=False,
            enforcement='kit commands/adapters only; external Desktop edits are detected at gates', **extra)

    def export(self, run, history):
        with PinnedTree(self.state) as tree:
            if not (self.state / 'hu-artifacts').exists():
                with tree.directory('hu-artifacts', create=True): pass
        # Atomic, replaceable derived export; SQLite is the durable source of truth.
        class Artifact:
            def model_dump(self): return dict(schema_version=1, run=run.model_dump(), history=history,
                artifact_sha256=sha(canonical(dict(run=run.model_dump(), history=history))))
        persist(self.state / 'hu-artifacts' / (run.story_id + '.json'), Artifact())

    def run(self, action, story, operation=None, payload=None):
        from .activity_ledger import ActivityLedger, now as activity_now
        self.refresh_selection()
        ledger=ActivityLedger(self.config['binding'])
        # Legacy 03 clients opt in with activity init. New setup clients require it.
        if action=='status' or (self.access is None and not ledger.path.exists()):
            return self._run(action,story,operation,payload)
        operation_id=sha(canonical(dict(story=story,operation=operation)))
        # The HU transaction remains authoritative for replay and final-persist repair.
        recorded=False
        if (self.state/'hu.sqlite3').exists():
            with sqlite3.connect((self.state/'hu.sqlite3').as_uri()+'?mode=ro',uri=True) as db:
                recorded=bool(db.execute('SELECT 1 FROM events WHERE story=? AND operation=?',(story,operation)).fetchone())
        if recorded:
            result=self._run(action,story,operation,payload)
            with ledger.database() as db:
                pending=db.execute('SELECT start_event FROM operations WHERE operation_id=? AND result_event IS NULL',(operation_id,)).fetchone()
            if pending:
                start=json.loads(pending[0]); key=sha((operation_id+'result').encode())
                ledger.ingest([{**start,'event_id':key,'idempotency_key':key,'kind':'result',
                    'observed_at':activity_now(),'status':'blocked' if result['status']=='blocked' else 'passed','duration_ms':None}])
            return result
        attempt=None
        if action!='start' and (self.state/'hu.sqlite3').exists():
            with sqlite3.connect((self.state/'hu.sqlite3').as_uri()+'?mode=ro',uri=True) as db:
                row=db.execute('SELECT payload FROM runs WHERE story=?',(story,)).fetchone()
                if row: attempt=json.loads(row[0])['attempt']
        if action=='attempt' and attempt is not None: attempt+=1
        if action=='start': attempt=1
        with ledger.operation(operation_id,scope='hu',hu_id=story,attempt=attempt,action=action) as outcome:
            result=self._run(action,story,operation,payload)
            outcome['status']='blocked' if result['status']=='blocked' else 'passed'
            run=result.get('run',{})
            outcome['candidate_sha256']=(run.get('candidate') or {}).get('candidate_sha256')
            outcome['revision']=(run.get('plan') or {}).get('revision')
            return result

    @with_hu_tools
    def refresh_selection(self):
        # Reload policy and binding at every adapter boundary, including reuse of
        # a service instance; changed selection never redirects its state silently.
        target,config=selected(self.target,self.policy_path,self.binding_path)
        b,original=config['binding'],self.config['binding']
        if (b.client_id,b.checkout_id,b.state_dir,target)!=(original.client_id,original.checkout_id,original.state_dir,self.target):
            raise ConfigError('hu_identity_mismatch')
        self.config=config
        self.access=self.load_access()

    @with_hu_tools
    def _run(self, action, story, operation=None, payload=None):
        self.refresh_selection()
        try:
            TypeAdapter(ID).validate_python(story, strict=True)
            if action != 'status': TypeAdapter(ID).validate_python(operation, strict=True)
        except ValidationError: raise ConfigError('invalid_hu_document') from None
        if action not in INPUTS and action != 'status': raise ConfigError('invalid_hu_action')
        data = parse(INPUTS[action], payload) if action != 'status' else None
        if action == 'start': preparation=self.prepared(data.onboarding_plan)
        request_hash = sha(canonical(dict(action=action, data=data.model_dump()))) if data else None
        with self.database(create=action == 'start',readonly=action=='status') as db:
            existing = db.execute('SELECT request_hash FROM events WHERE story=? AND operation=?', (story, operation)).fetchone()
            if existing and existing[0] != request_hash: raise ConfigError('hu_operation_conflict')
            if action == 'start' and not existing:
                if db.execute('SELECT 1 FROM runs WHERE story=?', (story,)).fetchone(): raise ConfigError('hu_story_exists')
                with PinnedTree(self.target) as tree:
                    run = HuRun(schema_version=1, story_id=story, run_id=uuid.uuid4().hex,
                        client_id=self.config['binding'].client_id, checkout_id=self.config['binding'].checkout_id,
                        target_identity=tree.base.identity(), onboarding_plan=data.onboarding_plan,writer_actor=data.writer_actor,
                        catalog=preparation.request.catalog,simulation=data.simulation,
                        context_sha256=self.context_hash(), base=git_read(self.target, 'rev-parse', 'HEAD'), baseline_files=baseline(self.target,self.access,self.config['policy']))
            else: run = self.load(db, story)
            current_context = self.context_hash()
            drift = run.context_sha256 != current_context
            if drift:
                run.context_sha256 = current_context
                run.approval, run.candidate, run.evidence, run.assignments = None, None, [], []
                if run.state not in ('cancelled','published'): run.state='planned'
                run.blocked_reason = 'context_changed'
            if action == 'status':
                # Status reports effective drift but is not an approval or evidence writer.
                if not drift and run.candidate:
                    try: run.blocked_reason=self.fresh_candidate(run) or run.blocked_reason
                    except ConfigError as error: run.blocked_reason=error.code.removeprefix('hu_')
                return self.response(run, 'blocked' if drift or run.blocked_reason else ('partial' if run.simulation and run.state=='ready_to_publish' else 'ready'), history=self.history(db, story))
            if existing:
                if not drift and run.candidate:
                    try: run.blocked_reason=self.fresh_candidate(run) or run.blocked_reason
                    except ConfigError as error: run.blocked_reason=error.code.removeprefix('hu_')
                if drift or run.blocked_reason:
                    db.execute('UPDATE runs SET payload=? WHERE story=?', (canonical(run.model_dump()).decode(), story))
                history = self.history(db, story)
                db.commit()
                self.export(run, history)
                return self.response(run, 'blocked' if run.blocked_reason else ('partial' if run.simulation and run.state=='ready_to_publish' else 'ready'), idempotent=True)
            before = run.state
            pending = db.execute('SELECT payload FROM pending WHERE story=?',(story,)).fetchone()
            if pending and action not in ('resume','worktree','status'):
                reason = 'recovery_required'
            else: reason = None
            if drift and action not in ('plan', 'resume', 'block'): reason = 'context_changed'
            if not reason:
                try: reason = self.apply_action(db, run, action, data)
                except ConfigError as error:
                    if error.code.startswith('hu_'): reason = error.code.removeprefix('hu_')
                    else: raise
            run.blocked_reason = reason
            status = 'blocked' if reason else ('partial' if run.simulation and run.state=='ready_to_publish' else 'ready')
            gate = GateResult(schema_version=1, gate=action, status='blocked' if reason else ('partial' if status=='partial' else 'passed'),
                reason=reason, candidate_sha256=run.candidate.candidate_sha256 if run.candidate else None)
            event = dict(schema_version=1, operation_id=operation, action=action, at=now(), before=before,
                after=run.state, status=status, gate=gate.model_dump(), request_sha256=request_hash,
                input=data.model_dump(), context_sha256=run.context_sha256,
                artifact=(run.plan.model_dump() if action=='plan' and run.plan else
                    run.candidate.model_dump() if action=='candidate' and run.candidate else None),
                attempt=run.attempt, revision=run.plan.revision if run.plan else None)
            run = parse(HuRun, run.model_dump())
            db.execute('INSERT OR REPLACE INTO runs VALUES (?, ?)', (story, canonical(run.model_dump()).decode()))
            db.execute('INSERT INTO events(story,operation,request_hash,payload) VALUES (?,?,?,?)',
                (story, operation, request_hash, canonical(event).decode()))
            checkpoint('before_commit')
            db.commit()
            checkpoint('after_commit')
            self.export(run, self.history(db, story))
            return self.response(run, status, gate, idempotent=False)

    def fresh_candidate(self, run):
        if not run.candidate: return 'candidate_required'
        try: after = capture(self.target, run, self.config['policy'],self.access)
        except ConfigError as error:
            run.candidate,run.evidence=None,[]
            run.state='implementing'
            return error.code.removeprefix('hu_')
        if after != run.candidate:
            run.candidate, run.evidence = None, []
            run.state = 'implementing'
            return 'candidate_changed'
        return None

    def apply_action(self, db, run, action, data):
        if action == 'start': return None
        if run.state in ('cancelled', 'published'): return 'terminal_state'
        if action == 'attempt':
            if run.state!='failed': return 'failed_attempt_required'
            self.prepared(run.onboarding_plan)
            run.baseline_files=baseline(self.target,self.access,self.config['policy'])
            run.base=git_read(self.target,'rev-parse','HEAD')
            run.attempt+=1
            run.corrections,run.delegations=0,0
            run.plan,run.approval,run.candidate=None,None,None
            run.evidence,run.assignments,run.handoffs=[],[],[]
            run.state='draft'
        elif action == 'plan':
            for path in data.paths:
                scope_write(self.access,self.config['policy'],path.rstrip('/')+('/scope-check' if path.endswith('/') else ''),data.paths)
                if denied(path.rstrip('/'), ['.git/', '.harness/', '.codex/', '.agents/'] + self.config['policy'].denied_paths + self.config['policy'].read_only_paths): return 'scope_denied'
            value = dict(**data.model_dump(), revision=run.plan.revision+1 if run.plan else 1, context_sha256=run.context_sha256)
            run.plan = parse(PlanRevision, {**value, 'plan_sha256':sha(canonical(value))})
            run.state, run.approval, run.candidate, run.evidence, run.assignments = 'planned', None, None, [], []
        elif action == 'approve':
            if run.state != 'planned' or not run.plan: return 'plan_required'
            if run.plan.context_sha256!=run.context_sha256: return 'new_plan_required'
            if not data.confirmed or (data.client_id,data.checkout_id,data.attempt,data.revision,data.plan_sha256) != (
                run.client_id,run.checkout_id,run.attempt,run.plan.revision,run.plan.plan_sha256): return 'approval_mismatch'
            run.approval = ApprovalRecord(**data.model_dump(), approved_at=now())
            run.state = 'approved'
        elif action in ('candidate','assign','correct','worktree'):
            if not approval_current(run): return 'approval_required'
            if action == 'candidate':
                if run.state not in ('approved','implementing','validating','reviewing','ready_to_publish'): return 'invalid_transition'
                try: current = capture(self.target, run, self.config['policy'],self.access)
                except ConfigError as error:
                    run.candidate,run.evidence=None,[]
                    run.state='implementing'
                    return error.code.removeprefix('hu_')
                if run.candidate != current: run.evidence = []
                run.candidate, run.state = current, 'implementing'
            elif action == 'correct':
                if run.corrections >= 2: return 'correction_limit'
                run.corrections += 1
                run.state, run.candidate, run.evidence = 'implementing', None, []
            elif action == 'assign':
                if run.delegations >= run.plan.max_delegations or len(run.assignments) >= 4: return 'delegation_limit'
                from harness_core.desktop import check_assignments
                try: check_assignments(run.catalog,[*run.assignments,data])
                except ConfigError as error: return error.code
                if data.delegation_depth > 1: return 'delegation_limit'
                if data.isolation != run.checkout_id: return 'isolation_mismatch'
                if data.write_paths and data.role not in ('principal','developer','tester'): return 'read_only_assignment'
                if any(not covers(p,run.plan.paths) for p in data.write_paths): return 'scope_denied'
                for row in db.execute('SELECT payload FROM runs'):
                    other = parse(HuRun,json.loads(row[0]))
                    if other.state in ('failed','cancelled','ready_to_publish','published'): continue
                    if other.story_id!=run.story_id and approval_current(other) and any(
                        covers(p,other.plan.paths) or covers(q,data.write_paths) for p in data.write_paths for q in other.plan.paths):
                        return 'writer_collision'
                    for assignment in other.assignments:
                        if any(covers(p,assignment.write_paths) or covers(q,data.write_paths) for p in data.write_paths for q in assignment.write_paths): return 'writer_collision'
                run.assignments.append(data)
                run.delegations += 1
            else: return self.worktree(db, run, data)
        elif action == 'evidence':
            if run.state not in ('validating','reviewing') and not (data.kind=='capability' and run.state=='implementing'):
                return 'invalid_transition'
            if not approval_current(run): return 'approval_required'
            reason = self.fresh_candidate(run)
            if reason: return reason
            if data.candidate_sha256 != run.candidate.candidate_sha256: return 'stale_evidence'
            run.evidence = [e for e in run.evidence if (e.id,e.kind) != (data.id,data.kind)] + [data]
        elif action == 'transition':
            allowed = {'draft':{'analyzing'}, 'analyzing':set(), 'planned':set(), 'approved':{'implementing'},
                'implementing':{'validating'}, 'validating':{'reviewing'}, 'reviewing':{'ready_to_publish'},
                'ready_to_publish':set(), 'failed':set()}
            if data.state == 'published': return 'publication_unavailable'
            if data.state in ('cancelled','failed'):
                run.state, run.assignments,run.candidate,run.evidence = data.state, [],None,[]
                return None
            if data.state != 'analyzing' and not approval_current(run): return 'approval_required'
            if data.state not in allowed.get(run.state,set()): return 'invalid_transition'
            if data.state in ('validating','reviewing','ready_to_publish'):
                reason = self.fresh_candidate(run)
                if reason: return reason
                # Capabilities must be actual observations even in simulation.
                records = {e.id:e for e in run.evidence if e.kind=='capability'}
                if any(key not in records or records[key].status!='passed' or records[key].simulated or
                    records[key].candidate_sha256!=run.candidate.candidate_sha256 for key in run.plan.required_capabilities): return 'capability_required'
            if data.state in ('reviewing','ready_to_publish'):
                reason = evidence_gate(run,'test',run.plan.tests)
                if reason: return reason
            if data.state == 'ready_to_publish':
                reviews = [e.id for e in run.evidence if e.kind=='review']
                if not reviews: return 'independent_review_required'
                reason = evidence_gate(run,'review',reviews)
                if reason: return reason
            run.state = data.state
        elif action == 'block': return data.reason
        elif action == 'resume':
            self.prepared(run.onboarding_plan)
            if run.plan and run.plan.context_sha256 != run.context_sha256:
                run.state, run.approval = 'planned', None
                return 'new_plan_required'
            if git_read(self.target,'rev-parse','HEAD') != run.base: return 'base_changed'
            for worktree in run.worktrees:
                path=safe_path(worktree.path)
                if not path.exists(): return 'worktree_mismatch'
                with PinnedTree(path) as tree:
                    if tree.base.identity()!=worktree.target_identity: return 'worktree_mismatch'
                if git_read(path,'rev-parse','HEAD')!=worktree.base: return 'worktree_mismatch'
                if git_read(path,'symbolic-ref','--short','HEAD')!=worktree.branch: return 'worktree_mismatch'
            pending = db.execute('SELECT payload FROM pending WHERE story=?',(run.story_id,)).fetchone()
            if pending:
                data = parse(INPUTS['worktree'],json.loads(pending[0]))
                reason = self.worktree(db,run,data,recover=True)
                if reason: return reason
            if run.candidate: return self.fresh_candidate(run)
        elif action == 'handoff':
            if not run.plan or data.plan_sha256 != run.plan.plan_sha256: return 'stale_plan'
            if data.candidate_sha256 is not None and (not run.candidate or data.candidate_sha256!=run.candidate.candidate_sha256): return 'stale_evidence'
            run.handoffs.append(data)
        return None

    def worktree(self, db, run, data, recover=False):
        if not run.plan.allow_worktrees or not data.confirmed: return 'worktree_denied'
        path = unmanaged_path(str(safe_path(data.path)))
        separate([str(path), str(self.target), str(self.state), str(self.policy_path), str(self.binding_path)])
        entries = git_read(self.target,'worktree','list','--porcelain').split('\n\n')
        match = any(('worktree '+path.as_posix()) in entry.splitlines() and
            ('branch refs/heads/'+data.branch) in entry.splitlines() for entry in entries)
        pending = db.execute('SELECT payload FROM pending WHERE story=?',(run.story_id,)).fetchone()
        if pending and json.loads(pending[0]) != data.model_dump(): return 'pending_operation_mismatch'
        recorded=next((w for w in run.worktrees if safe_path(w.path)==path),None)
        if match and not pending and not recorded: return 'worktree_exists'
        if not match:
            if recover: return 'worktree_pending_not_applied'
            if path.exists(): return 'worktree_exists'
            safe_path(path.parent)
            if not path.parent.is_dir(): return 'worktree_parent_missing'
            # Freeze intent BEFORE the only filesystem side effect. A retry observes
            # the registered branch/path/base, never repeats a confirmed creation.
            db.execute('INSERT OR REPLACE INTO pending VALUES (?,?)',(run.story_id,canonical(data.model_dump()).decode()))
            db.commit()
            checkpoint('worktree_intent')
            db.execute('BEGIN IMMEDIATE')
            import re
            overrides = ['-c','core.hooksPath=NUL']
            try: keys=git_read(self.target,'config','--name-only','--get-regexp',r'^filter\.').splitlines()
            except ConfigError as error:
                if error.code!='probe_failed': raise
                keys=[]
            for key in keys:
                found=re.fullmatch(r'filter\.([A-Za-z0-9_.-]+)\.[A-Za-z0-9_-]+',key)
                if not found: return 'filter_not_verified'
                for suffix,value in (('clean',''),('smudge',''),('process',''),('required','false')):
                    overrides.extend(['-c',f'filter.{found.group(1)}.{suffix}={value}'])
            try:
                with PinnedTree(path.parent):
                    git_read(self.target,'worktree','add','-b',data.branch,str(path),run.base,overrides=overrides)
            except ConfigError: return 'worktree_infrastructure_failure'
            checkpoint('worktree_created')
        if git_read(path,'rev-parse','HEAD') != run.base: return 'worktree_mismatch'
        if not recorded:
            with PinnedTree(path) as tree:
                run.worktrees.append(WorktreeRecord(**data.model_dump(),target_identity=tree.base.identity(),base=run.base))
        db.execute('DELETE FROM pending WHERE story=?',(run.story_id,))
        return None
