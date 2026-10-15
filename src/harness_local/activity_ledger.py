"""Durable own-operation ledger. Reads never initialize, migrate, lock or journal."""
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import time
import uuid

from pydantic import ValidationError

from harness_core.activity import ActivityEvent, UsageObservation, LedgerQuery, LedgerReport
from harness_core.configuration import ConfigError, safe_path
from harness_core.onboarding_plan import canonical, sha, separate
from .execution_state import ensure_state
from .windows_fs import PinnedTree


def now():
    return datetime.now(timezone.utc).isoformat()


class ActivityLedger:
    def __init__(self, binding):
        self.binding = binding
        self.state = safe_path(binding.state_dir)
        self.path = self.state / 'activity.sqlite3'
        separate([binding.target_path, binding.state_dir])
        self.identity = dict(client_id=binding.client_id, checkout_id=binding.checkout_id,
            binding_sha256=sha(canonical(binding.model_dump())))

    @contextmanager
    def database(self, *, write=False, initialize=False, legacy=False):
        if initialize: ensure_state(self.binding)
        if not self.path.exists() and not initialize: raise ConfigError('ledger_missing')
        try:
            with PinnedTree(self.state):
                for name in ('activity.sqlite3', 'activity.sqlite3-journal', 'activity.sqlite3-wal', 'activity.sqlite3-shm'):
                    p = safe_path(self.state / name)
                    if p.exists() and (not p.is_file() or p.stat().st_nlink != 1):
                        raise ConfigError('ledger_unavailable')
                uri = self.path.as_uri() + ('?mode=rwc' if initialize else '?mode=rw' if write else '?mode=ro')
                db = sqlite3.connect(uri, uri=True, timeout=0.25, isolation_level=None)
                try:
                    if write: db.execute('PRAGMA synchronous=FULL'); db.execute('BEGIN IMMEDIATE')
                    version = db.execute('PRAGMA user_version').fetchone()[0]
                    if version == 0 and initialize:
                        if db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]:
                            raise ConfigError('ledger_schema_unsupported')
                        db.execute('CREATE TABLE ledger_metadata (payload TEXT NOT NULL)')
                        db.execute('INSERT INTO ledger_metadata VALUES (?)', (canonical(self.identity).decode(),))
                        db.execute('CREATE TABLE activity_events (source TEXT, event_id TEXT, operation_id TEXT, idempotency_key TEXT, payload TEXT NOT NULL, PRIMARY KEY(source,idempotency_key), UNIQUE(source,event_id))')
                        db.execute('CREATE TABLE operations (operation_id TEXT PRIMARY KEY, source TEXT NOT NULL, start_event TEXT, result_event TEXT)')
                        db.execute('CREATE TABLE usage_observations (source TEXT, source_event_id TEXT, payload TEXT NOT NULL, PRIMARY KEY(source,source_event_id))')
                        db.execute('CREATE TABLE coverage (source TEXT PRIMARY KEY, status TEXT NOT NULL)')
                        db.executemany('INSERT INTO coverage VALUES (?,?)', [('harness_commands','enabled'), ('hooks','native_actions_not_observed'), ('imported','submitted_events_only'), ('desktop_usage','supported_attributable_source_unavailable')])
                        db.execute('CREATE INDEX events_operation ON activity_events(operation_id)')
                        db.execute('PRAGMA user_version=2')
                    elif version != 2 and not (legacy and version==1): raise ConfigError('ledger_schema_unsupported')
                    row = db.execute('SELECT payload FROM ledger_metadata').fetchone()
                    if not row or json.loads(row[0]) != self.identity: raise ConfigError('ledger_identity_mismatch')
                    yield db
                    if db.in_transaction: db.commit()
                except BaseException:
                    if db.in_transaction: db.rollback()
                    raise
                finally: db.close()
        except sqlite3.Error as error:
            raise ConfigError('ledger_busy' if getattr(error,'sqlite_errorcode',None) in (5,6) else 'ledger_unavailable') from None
        except OSError:
            raise ConfigError('ledger_unavailable') from None

    def initialize(self):
        with self.database(write=True, initialize=True): pass

    def migrate(self, backup):
        backup=safe_path(backup)
        separate([backup,self.path,self.binding.target_path])
        with self.database(write=True,legacy=True) as db:
            if db.execute('PRAGMA user_version').fetchone()[0]==2: return
            # An exclusive snapshot is durable before any schema mutation.
            with PinnedTree(backup.parent) as tree:
                with tree.file(backup.name,create=True) as handle: handle.write(db.serialize())
            db.execute('CREATE INDEX IF NOT EXISTS events_operation ON activity_events(operation_id)')
            db.execute('PRAGMA user_version=2')

    def check_identity(self, value):
        if (value.client_id, value.checkout_id) != (self.binding.client_id, self.binding.checkout_id):
            raise ConfigError('ledger_identity_mismatch')

    def import_setup_journal(self, run_id, journal):
        marker='setup-journal-'+run_id
        fingerprint=sha(canonical(journal))
        with self.database() as db:
            row=db.execute('SELECT status FROM coverage WHERE source=?',(marker,)).fetchone()
        if row:
            if row[0] not in (fingerprint,'harness_commands'): raise ConfigError('event_id_conflict')
            return
        events=[]
        for stage in journal.get('stages',[]):
            if stage['status'] not in ('completed','failed'): continue
            operation=sha(canonical(dict(run=run_id,plan=journal['plan_sha256'],stage=stage['name'])))
            with self.database() as db:
                # Event keys are independent of import arrival time.
                key=sha((operation+'start').encode())
                row=db.execute('SELECT payload FROM activity_events WHERE source=? AND idempotency_key=?',('imported',key)).fetchone()
            at=json.loads(row[0])['observed_at'] if row else now()
            base=dict(schema_version=1,client_id=self.binding.client_id,checkout_id=self.binding.checkout_id,
                operation_id=operation,source='imported',scope='setup',action=stage['name'],observed_at=at,
                payload={'setup_journal_imported':True})
            events.append(dict(**base,event_id=key,idempotency_key=key,kind='start'))
            key=sha((operation+'result').encode())
            events.append(dict(**base,event_id=key,idempotency_key=key,kind='result',status='passed' if stage['status']=='completed' else 'failed'))
        self.ingest(events)
        with self.database(write=True) as db:
            db.execute('INSERT INTO coverage VALUES (?,?)',(marker,fingerprint))

    def ingest(self, events=(), usage=()):
        try:
            events = [ActivityEvent.model_validate(e.model_dump() if isinstance(e,ActivityEvent) else e) for e in events]
            usage = [UsageObservation.model_validate(u.model_dump() if isinstance(u,UsageObservation) else u) for u in usage]
        except ValidationError: raise ConfigError('event_invalid') from None
        for item in [*events,*usage]: self.check_identity(item)
        with self.database(write=True) as db:
            for event in events:
                data=canonical(event.model_dump()).decode()
                rows=db.execute('SELECT payload FROM activity_events WHERE source=? AND (idempotency_key=? OR event_id=?)',
                    (event.source,event.idempotency_key,event.event_id)).fetchall()
                if rows:
                    if any(row[0]!=data for row in rows): raise ConfigError('event_id_conflict')
                    continue
                if event.source != 'hooks' and event.kind in ('start','result'):
                    row=db.execute('SELECT source,start_event,result_event FROM operations WHERE operation_id=?',(event.operation_id,)).fetchone()
                    if row and row[0]!=event.source: raise ConfigError('event_id_conflict')
                    if row:
                        association=json.loads(row[1] or row[2])
                        if any(association[key]!=getattr(event,key) for key in ('scope','hu_id','attempt','role')):
                            raise ConfigError('activity_association_mismatch')
                    if not row: db.execute('INSERT INTO operations VALUES (?,?,NULL,NULL)',(event.operation_id,event.source))
                    field='start_event' if event.kind=='start' else 'result_event'
                    existing=db.execute('SELECT '+field+' FROM operations WHERE operation_id=?',(event.operation_id,)).fetchone()[0]
                    if existing: raise ConfigError('event_id_conflict')
                    db.execute('UPDATE operations SET '+field+'=? WHERE operation_id=?',(data,event.operation_id))
                db.execute('INSERT INTO activity_events VALUES (?,?,?,?,?)',(event.source,event.event_id,event.operation_id,event.idempotency_key,data))
            for observation in usage:
                data=canonical(observation.model_dump()).decode()
                row=db.execute('SELECT payload FROM usage_observations WHERE source=? AND source_event_id=?',(observation.source,observation.source_event_id)).fetchone()
                if row:
                    if row[0]!=data: raise ConfigError('event_id_conflict')
                else: db.execute('INSERT INTO usage_observations VALUES (?,?,?)',(observation.source,observation.source_event_id,data))

    @contextmanager
    def operation(self, operation_id, *, scope, hu_id=None, attempt=None, role=None, action=None, request_sha256=None):
        # Stable id + durable start blocks blind replay after interruption.
        with self.database() as db:
            row=db.execute('SELECT result_event FROM operations WHERE operation_id=?',(operation_id,)).fetchone()
        if row: raise ConfigError('ledger_operation_completed' if row[0] else 'ledger_recovery_required')
        base=dict(schema_version=1,client_id=self.binding.client_id,checkout_id=self.binding.checkout_id,
            operation_id=operation_id,scope=scope,hu_id=hu_id,attempt=attempt,role=role,action=action,
            request_sha256=request_sha256,source='harness_commands')
        def event(kind, **extra):
            key=sha((operation_id+kind).encode())
            return dict(**base,event_id=key,idempotency_key=key,kind=kind,observed_at=now(),**extra)
        self.ingest([event('start')])
        started=time.monotonic()
        try:
            outcome = {}
            yield outcome
        except (SystemExit,KeyboardInterrupt):
            raise
        except BaseException:
            # If the result cannot persist, the durable start remains pending.
            self.ingest([event('result',status='failed',duration_ms=(time.monotonic()-started)*1000)])
            raise
        else:
            if not outcome.get('pending'):
                self.ingest([event('result',status=outcome.get('status','passed'),duration_ms=(time.monotonic()-started)*1000,
                    candidate_sha256=outcome.get('candidate_sha256'),revision=outcome.get('revision'))])

    def finish_pending(self, operation_id, status):
        with self.database() as db:
            row=db.execute('SELECT start_event FROM operations WHERE operation_id=? AND result_event IS NULL',(operation_id,)).fetchone()
        if row:
            event=json.loads(row[0]); key=sha((operation_id+'result').encode())
            self.ingest([{**event,'event_id':key,'idempotency_key':key,'kind':'result',
                'observed_at':now(),'status':status,'duration_ms':None}])

    def report(self, query=None):
        try: query=LedgerQuery.model_validate(query or {'schema_version':1})
        except ValidationError: raise ConfigError('invalid_ledger_query') from None
        if query.client_id not in (None,self.binding.client_id) or query.checkout_id not in (None,self.binding.checkout_id):
            raise ConfigError('ledger_identity_mismatch')
        def accepts(e):
            return all(getattr(query,k) is None or e.get(k)==getattr(query,k) for k in ('hu_id','attempt','role')) and (
                query.since is None or datetime.fromisoformat(e['observed_at'])>=datetime.fromisoformat(query.since)) and (
                query.until is None or datetime.fromisoformat(e['observed_at'])<=datetime.fromisoformat(query.until))
        with self.database() as db:
            events=[json.loads(row[0]) for row in db.execute('SELECT payload FROM activity_events ORDER BY rowid')]
            usage=[json.loads(row[0]) for row in db.execute('SELECT payload FROM usage_observations ORDER BY rowid')]
            coverage=dict(db.execute('SELECT source,status FROM coverage'))
        events=[e for e in events if accepts(e)]; usage=[u for u in usage if accepts({**u,'role':None})]
        starts={e['operation_id'] for e in events if e['kind']=='start' and e['source']!='hooks'}
        results={e['operation_id']:e for e in events if e['kind']=='result' and e['source']!='hooks'}
        conflicts=[]
        for i,u in enumerate(usage):
            for v in usage[:i]:
                if u['native_session_id'] and u['native_session_id']==v['native_session_id'] and u['source']==v['source'] and u['surface']==v['surface'] and max(datetime.fromisoformat(u['period_start']),datetime.fromisoformat(v['period_start']))<=min(datetime.fromisoformat(u['period_end']),datetime.fromisoformat(v['period_end'])):
                    conflicts.append('overlapping_usage_scopes')
        return LedgerReport(schema_version=1,client_id=self.binding.client_id,checkout_id=self.binding.checkout_id,
            events=events,usage=usage,counts=dict(Counter(e['kind'] for e in events if e['source']!='hooks' or e['operation_id'] not in starts|results.keys())),
            incomplete_operations=len(starts-results.keys()),failed_operations=sum(e['status']=='failed' for e in results.values()),
            duration_ms=sum(e['duration_ms'] or 0 for e in results.values()),coverage=coverage,
            incomplete_durations=len(starts-results.keys())+sum(e['duration_ms'] is None for e in results.values()),
            blocked_operations=sum(e['status']=='blocked' for e in results.values()),retries=sum(e['kind']=='retry' for e in events),
            measurement_conflicts=sorted(set(conflicts))).model_dump()

    def export(self, path, query=None):
        path=safe_path(path)
        separate([path,self.path,self.binding.target_path])
        data=canonical(self.report(query))+b'\n'
        with PinnedTree(path.parent) as tree:
            with tree.file(path.name,create=True) as handle: handle.write(data)
