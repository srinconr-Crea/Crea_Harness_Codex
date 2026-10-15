"""Preview and durable publication reconciliation, separate from HU/onboarding v1."""
from contextlib import contextmanager
import json
import sqlite3

from harness_core.configuration import ConfigError, safe_path
from harness_core.hu import approval_current, evidence_gate
from harness_core.onboarding_plan import canonical, sha, separate
from harness_core.story import PublicationIntent, PublicationAuthorization, PublicationReceipt, StoryPlanBinding, reconcile_story
from .execution_state import CheckoutLock
from .windows_fs import PinnedTree
from .story_providers import marker, require
from harness_core.guided import SafeContract
from .evaluation_service import EvalInput


class PublicationRequest(SafeContract):
    intent: PublicationIntent
    authorization: PublicationAuthorization | None
    evaluation: EvalInput | None


def parse(model, raw):
    try: return model.model_validate(raw)
    except ValueError: raise ConfigError('invalid_publication_document') from None


def authorization_gate(value, approval):
    if not approval or not approval.confirmed or approval.intent_sha256 != value.intent_sha256 or set(approval.actions) != {'push', 'create_pr'}:
        return 'publication_authorization_required'


def evaluation_gate(value):
    if value is None: return 'required_evaluations_not_run'
    from .evaluation_service import dispatch
    from harness_core.evaluation import EvalProfile
    request = value.model_dump() if hasattr(value, 'model_dump') else value
    if request.get('milestone') != 7 or request.get('purpose') != 'promotion': return 'publication_evaluation_scope'
    report, _ = dispatch('report', request)
    # A report is recomputed from annotations, never accepted as a supplied passed flag.
    if not report['promotion_allowed']: return 'required_evaluations_blocked'


def bind_story(hu, value):
    """Explicit technical approval of a story/plan link; immutable for that plan hash."""
    from .activity_execution import run
    context=None
    if hu.access or (hu.state/'activity.sqlite3').exists():
        context=dict(schema_version=1,target_path=str(hu.target),policy_path=str(hu.policy_path),
            binding_path=str(hu.binding_path),hu_id=value.hu_id,attempt=value.attempt,
            operation_id=sha(canonical(value.model_dump())))
    return run(context,'story_bind',lambda:_bind_story(hu,value),expected_binding=hu.config['binding'],
        reconciler=True,reconcile_success=('ready',),request_sha256=sha(canonical(value.model_dump())))


def _bind_story(hu, value):
    value = parse(StoryPlanBinding, value.model_dump())
    with hu.database() as db:
        run = hu.load(db, value.hu_id)
    if not value.confirmed or not approval_current(run): raise ConfigError('story_plan_approval_required')
    if (value.client_id, value.checkout_id, value.attempt, value.plan_sha256, value.story.repository) != (
        run.client_id, run.checkout_id, run.attempt, run.plan.plan_sha256, hu.config['policy'].repository):
        raise ConfigError('story_plan_binding_mismatch')
    if hu.context_hash() != run.context_sha256: raise ConfigError('context_changed')
    with PinnedTree(hu.state), CheckoutLock(hu.state, 'story-source', recover=True):
        path = safe_path(hu.state/'story-sources.sqlite3')
        for suffix in ('','-journal','-wal','-shm'):
            p = safe_path(str(path)+suffix)
            if p.exists() and (not p.is_file() or p.stat().st_nlink != 1): raise ConfigError('story_source_conflict')
        with sqlite3.connect(path, timeout=1) as db:
            db.execute('PRAGMA synchronous=FULL')
            version=db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0,1): raise ConfigError('story_source_version')
            if version==0:
                if db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]: raise ConfigError('story_source_version')
                db.execute('CREATE TABLE sources (hu TEXT, attempt INTEGER, plan TEXT, payload TEXT, PRIMARY KEY(hu,attempt,plan))')
                db.execute('PRAGMA user_version=1')
            key=(value.hu_id,value.attempt,value.plan_sha256)
            row=db.execute('SELECT payload FROM sources WHERE hu=? AND attempt=? AND plan=?',key).fetchone()
            if row and parse(StoryPlanBinding,json.loads(row[0])) != value: raise ConfigError('story_plan_binding_immutable')
            if not row: db.execute('INSERT INTO sources VALUES (?,?,?,?)',(*key,canonical(value.model_dump()).decode()))
    return dict(schema_version=1,command='story',status='ready',checks=[],binding=value.model_dump(),
        publication_allowed=False,certified=False)


def source_gate(hu, value):
    path=safe_path(hu.state/'story-sources.sqlite3')
    if not path.exists(): return 'story_plan_binding_required'
    with PinnedTree(hu.state) as tree, tree.file(path.name):
        db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=1)
        try:
            if db.execute('PRAGMA user_version').fetchone()[0]!=1: return 'story_source_version'
            row=db.execute('SELECT payload FROM sources WHERE hu=? AND attempt=? AND plan=?',
                (value.hu_id,value.attempt,value.plan_sha256)).fetchone()
        finally: db.close()
    if not row: return 'story_plan_binding_required'
    binding=parse(StoryPlanBinding,json.loads(row[0]))
    if not binding.confirmed or (binding.client_id,binding.checkout_id,binding.story)!=(value.client_id,value.checkout_id,value.story):
        return 'story_plan_binding_mismatch'


def preview(value, approval=None, evaluation=None, *, export=None, target=None, protected=()):
    value = parse(PublicationIntent, value.model_dump())
    reason = authorization_gate(value, approval) or evaluation_gate(evaluation)
    result = dict(schema_version=1, command='pr', status='partial', checks=[],
        title=value.title, body=value.body + '\n\n' + marker(value), draft=True,
        candidate_sha256=value.candidate_sha256, evidence_refs=value.evidence_refs,
        intent=value.model_dump(), publication_allowed=False, certified=False,
        publication_gate='blocked' if reason else 'not_checked', reason=reason or 'final_candidate_not_checked')
    if export:
        if target is None: raise ConfigError('publication_target_required')
        out = safe_path(export)
        separate([str(out), str(safe_path(target)), *[str(safe_path(p)) for p in protected]])
        with PinnedTree(out.parent) as tree:
            with tree.file(out.name, create=True) as handle: handle.write(canonical(result) + b'\n')
    return result


def candidate_gate(hu, value):
    """Verify the committed tree against the frozen approved HU including specs/evidence."""
    from .diagnostics import git_read, local_status
    from .hu import git_names
    with hu.database() as db:
        run = hu.load(db, value.hu_id)
    b, policy = hu.config['binding'], hu.config['policy']
    if (value.client_id, value.checkout_id, value.attempt) != (b.client_id, b.checkout_id, run.attempt): return 'publication_identity_mismatch'
    if value.repository != policy.repository or value.base_branch != policy.base_branch: return 'publication_identity_mismatch'
    if not value.head_branch.startswith(policy.branch_prefix): return 'publication_branch_denied'
    if run.simulation: return 'simulated_candidate'
    if run.state != 'ready_to_publish' or run.blocked_reason: return 'candidate_not_ready'
    if not approval_current(run): return 'approval_required'
    reason=source_gate(hu,value)
    if reason: return reason
    if hu.context_hash() != value.context_sha256 or run.context_sha256 != value.context_sha256: return 'context_changed'
    if not run.candidate or (run.candidate.candidate_sha256, run.plan.plan_sha256, run.base) != (
        value.candidate_sha256, value.plan_sha256, value.base_oid): return 'candidate_changed'
    for kind, ids in (('test', run.plan.tests), ('review', [e.id for e in run.evidence if e.kind == 'review']),
                      ('capability', run.plan.required_capabilities)):
        if kind == 'review' and not ids: return 'independent_review_required'
        reason = evidence_gate(run, kind, ids)
        if reason: return reason
    records = {e.evidence_ref for e in run.evidence if e.status == 'passed' and not e.simulated and e.candidate_sha256 == value.candidate_sha256}
    if not set(value.evidence_refs) <= records: return 'publication_evidence_mismatch'
    if git_read(hu.target, 'rev-parse', 'HEAD') != value.head_oid or local_status(hu.target).code != 'clean': return 'candidate_changed'
    if git_read(hu.target, 'rev-parse', value.head_oid + '^') != value.base_oid: return 'publication_history_mismatch'
    # Whole-tree comparison also catches added/modified specs or evidence after approval.
    expected = dict(run.baseline_files)
    expected_modes = {}
    for line in git_names(hu.target, 'ls-tree', '-r', '-z', value.base_oid):
        if line:
            metadata, path = line.split('\t', 1)
            expected_modes[path] = metadata.split()[0]
    for entry in run.candidate.entries:
        if entry.operation == 'delete':
            expected.pop(entry.path, None); expected_modes.pop(entry.path, None)
        else:
            expected[entry.path] = entry.content_sha256
            expected_modes[entry.path] = entry.index_mode or expected_modes.get(entry.path, '100644')
    actual, actual_modes = {}, {}
    # cat-file outputs binary bytes; no filters, hooks, textconv or client code.
    import os, shutil, subprocess
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR'): env.pop(key, None)
    executable = shutil.which('git')
    try: autocrlf=git_read(hu.target,'config','--get','core.autocrlf').lower()
    except ConfigError as error:
        if error.code!='probe_failed': raise
        autocrlf='false'
    total = 0
    for line in git_names(hu.target, 'ls-tree', '-r', '-z', value.head_oid):
        if not line: continue
        metadata, path = line.split('\t', 1); mode, kind, oid = metadata.split()
        if mode not in ('100644', '100755') or kind != 'blob': return 'publication_entry_unsupported'
        size = int(git_read(hu.target, 'cat-file', '-s', oid)); total += size
        if size > 2*1024*1024 or total > 16*1024*1024 or len(actual) >= 4096: return 'publication_tree_too_large'
        try:
            raw = subprocess.run([executable, '-c', 'core.fsmonitor=false', '-C', str(hu.target), 'cat-file', 'blob', oid],
                env=env, capture_output=True, check=True, timeout=10).stdout
        except (OSError, subprocess.SubprocessError): return 'publication_tree_unavailable'
        with PinnedTree(hu.target) as tree:
            with tree.file(path) as handle: checkout_bytes=handle.read(2*1024*1024)
        attrs=git_read(hu.target,'check-attr','-z','text','eol','filter','working-tree-encoding','--',path).split('\0')
        attrs={attrs[n+1]:attrs[n+2] for n in range(0,len(attrs)-2,3)}
        if any(attrs.get(a,'unspecified') not in ('unspecified','unset') for a in ('filter','working-tree-encoding')):
            return 'publication_transform_unsupported'
        text=attrs.get('text','unspecified')
        normalize=(text in ('set','auto') or attrs.get('eol') in ('lf','crlf') or autocrlf in ('true','input')) and text!='unset'
        normalized=checkout_bytes.replace(b'\r\n',b'\n') if normalize and (text=='set' or b'\0' not in checkout_bytes) else checkout_bytes
        if raw != normalized: return 'candidate_changed'
        actual[path] = sha(checkout_bytes)
        actual_modes[path] = mode
    if expected != actual or expected_modes != actual_modes: return 'candidate_changed'


class PublicationService:
    def __init__(self, binding, provider, state_dir, *, candidate_check, evaluation_check=evaluation_gate, attach=None, activity_context=None):
        self.binding, self.provider, self.state = binding, provider, safe_path(state_dir)
        self.candidate_check, self.evaluation_check, self.attach = candidate_check, evaluation_check, attach
        self.activity_context=activity_context

    @contextmanager
    def database(self):
        if not self.state.is_dir(): raise ConfigError('publication_state_required')
        with PinnedTree(self.state), CheckoutLock(self.state, 'publication', recover=True):
            for suffix in ('', '-journal', '-wal', '-shm'):
                p = safe_path(self.state / ('publication.sqlite3' + suffix))
                if p.exists() and (not p.is_file() or p.stat().st_nlink != 1): raise ConfigError('publication_state_conflict')
            db = sqlite3.connect(self.state / 'publication.sqlite3', isolation_level=None, timeout=1)
            try:
                db.execute('PRAGMA synchronous=FULL')
                version = db.execute('PRAGMA user_version').fetchone()[0]
                if version not in (0, 1): raise ConfigError('publication_state_version')
                if version == 0:
                    if db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]: raise ConfigError('publication_state_version')
                    db.execute('CREATE TABLE receipts (id TEXT PRIMARY KEY, repository TEXT NOT NULL, branch TEXT NOT NULL, payload TEXT NOT NULL, UNIQUE(repository,branch))')
                    db.execute('PRAGMA user_version=1')
                yield db
            except sqlite3.Error: raise ConfigError('publication_state_conflict') from None
            finally: db.close()

    def gate(self, value, approval, evaluation):
        b = self.binding
        if (value.client_id, value.checkout_id, value.provider, value.repository, value.base_branch) != (
            b.client_id, b.checkout_id, b.provider, b.repository, b.base_branch): return 'publication_identity_mismatch'
        require(b, 'read_story'); require(b, 'push'); require(b, 'create_pr')
        return authorization_gate(value, approval) or self.candidate_check(value) or self.evaluation_check(evaluation)

    def publish(self, value, approval, evaluation):
        from .activity_execution import run
        return run(self.activity_context,'publication',lambda:self._publish(value,approval,evaluation),
            expected_identity=(value.client_id,value.checkout_id),reconciler=True,request_sha256=value.intent_sha256)

    def _publish(self, value, approval, evaluation):
        value = parse(PublicationIntent, value.model_dump())
        if approval: approval = parse(PublicationAuthorization, approval.model_dump())
        receipt = None
        def response(status, reason=None, attachment='unavailable'):
            return dict(schema_version=1, command='pr', status=status, checks=[], reason=reason,
                receipt=receipt.model_dump() if receipt else None, attachment_status=attachment,
                publication_allowed=status == 'published' and not self.provider.simulated,
                simulated=self.provider.simulated, certified=False)
        try:
            reason = self.gate(value, approval, evaluation)
            if reason: return response('blocked', reason)
            self.provider.preflight(self.binding)
            current = self.provider.read_story(self.binding, value.story.source_id)
            if reconcile_story(value.story, current): return response('blocked', 'story_changed')
            if self.provider.branch(self.binding, value.base_branch) != value.base_oid: return response('blocked', 'base_changed')
            with self.database() as db:
                row = db.execute('SELECT payload FROM receipts WHERE id=?', (value.intent_id,)).fetchone()
                if row:
                    receipt = parse(PublicationReceipt, json.loads(row[0]))
                    if receipt.intent != value: return response('blocked', 'publication_intent_conflict')
                def save(status, pr=None):
                    nonlocal receipt
                    attached = bool(receipt and receipt.attached and pr and receipt.pr_number == pr['number'])
                    receipt = PublicationReceipt(schema_version=1, intent=value, status=status,
                        pr_number=pr['number'] if pr else None, pr_url=pr['html_url'] if pr else None, attached=attached)
                    db.execute('INSERT OR REPLACE INTO receipts VALUES (?,?,?,?)',
                        (value.intent_id, value.repository, value.head_branch, canonical(receipt.model_dump()).decode()))
                # Branch ownership is unique across all intents, even on a lost response.
                other = db.execute('SELECT id FROM receipts WHERE repository=? AND branch=?', (value.repository, value.head_branch)).fetchone()
                if other and other[0] != value.intent_id: return response('blocked', 'foreign_branch')
                remote = self.provider.branch(self.binding, value.head_branch)
                prs = self.provider.prs(self.binding, value)
                if len(prs) > 1: return response('blocked', 'duplicate_remote_pr')
                if prs:
                    p = prs[0]
                    if (not self.matches(p, value) or remote != value.head_oid): return response('blocked', 'foreign_pr')
                    save('published', p)
                else:
                    if receipt and receipt.status == 'published': return response('blocked', 'published_pr_missing')
                    if remote is not None and (remote != value.head_oid or receipt is None): return response('blocked', 'foreign_branch')
                    if remote is None:
                        if receipt is not None and receipt.status not in ('pending', 'unknown'):
                            return response('blocked', 'remote_branch_missing')
                        reason = self.gate(value, approval, evaluation)
                        if reason: return response('blocked', reason)
                        save('pending')  # durable before any remote mutation
                        try: self.provider.push(self.binding, value)
                        except (ConfigError, OSError, ValueError): save('unknown'); return response('unknown', 'reconcile_required')
                        if self.provider.branch(self.binding, value.head_branch) != value.head_oid:
                            save('unknown'); return response('unknown', 'reconcile_required')
                        save('pushed')
                    reason = self.gate(value, approval, evaluation)
                    if reason: return response('blocked', reason)
                    # Refetch after push; do not publish against a changed base/source.
                    if self.provider.branch(self.binding, value.base_branch) != value.base_oid: return response('blocked', 'base_changed')
                    if reconcile_story(value.story, self.provider.read_story(self.binding, value.story.source_id)):
                        return response('blocked', 'story_changed')
                    prs = self.provider.prs(self.binding, value)
                    if len(prs) > 1: return response('blocked', 'duplicate_remote_pr')
                    if prs:
                        p = prs[0]
                        if not self.matches(p, value): return response('blocked', 'foreign_pr')
                    else:
                        try: p = self.provider.create_pr(self.binding, value)
                        except (ConfigError, OSError, ValueError): save('unknown'); return response('unknown', 'reconcile_required')
                    if not self.matches(p, value): save('unknown'); return response('unknown', 'reconcile_required')
                    save('published', p)
                reason = self.gate(value, approval, evaluation)
                if reason: return response('blocked', reason)
                if self.attach and not receipt.attached:
                    try:
                        if self.attach(receipt.pr_url) is not True: raise ConfigError('attachment_failed')
                        receipt.attached = True
                        db.execute('UPDATE receipts SET payload=? WHERE id=?', (canonical(receipt.model_dump()).decode(), value.intent_id))
                    except (ConfigError, OSError, ValueError): return response('published', 'attachment_failed', 'failed')
                return response('published', attachment='attached' if receipt.attached else 'unavailable')
        except ConfigError as error: return response('blocked', error.code)
        except sqlite3.Error: return response('blocked', 'story_source_conflict')
        except (KeyError, TypeError, ValueError): return response('blocked', 'provider_response_invalid')

    @staticmethod
    def matches(p, value):
        try:
            return (type(p['number']) is int and p['number'] > 0 and p['state'] == 'open' and p['draft'] is True and
                p['html_url'] == f'https://github.com/{value.repository}/pull/{p["number"]}' and
                marker(value) in p['body'] and p['head']['sha'] == value.head_oid and
                p['head']['ref'] == value.head_branch and p['base']['ref'] == value.base_branch and
                p['base']['sha'] == value.base_oid and
                p['head']['repo']['full_name'] == p['base']['repo']['full_name'] == value.repository)
        except (KeyError, TypeError): return False
