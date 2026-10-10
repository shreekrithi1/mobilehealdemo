"""Durable SQLite records and application audit trail (not tamper-proof)."""
import json
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

class Conflict(RuntimeError):
    pass

TRANSITIONS = {
 'pending': {'running','cancelled'},
 'running': {'reviewing','blocked','interrupted','cancelled'},
 'reviewing': {'completed','blocked','interrupted','cancelled'},
 'blocked': {'running','cancelled'},
 'interrupted': {'blocked','cancelled'},
 'completed': set(), 'cancelled': set(),
}

class HarnessStore:
    def __init__(self, path):
        self.path=str(Path(path).resolve())
        Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        with self._db() as c:
            c.executescript('''
            CREATE TABLE IF NOT EXISTS harness_runs(id TEXT PRIMARY KEY, request_id TEXT NOT NULL,
              input_revision TEXT NOT NULL, policy_version TEXT NOT NULL, idempotency_key TEXT UNIQUE NOT NULL,
              revision INTEGER NOT NULL, state TEXT NOT NULL, workspace TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS harness_events(seq INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, payload TEXT,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS harness_stages(run_id TEXT, stage TEXT, round INTEGER, payload TEXT,
              PRIMARY KEY(run_id,stage,round));
            CREATE TABLE IF NOT EXISTS harness_mutations(run_id TEXT, mutation_key TEXT, status TEXT, receipt TEXT,
              PRIMARY KEY(run_id,mutation_key));
            CREATE UNIQUE INDEX IF NOT EXISTS harness_mutation_identity ON harness_mutations(mutation_key);
            CREATE TABLE IF NOT EXISTS harness_locks(workspace TEXT PRIMARY KEY, run_id TEXT NOT NULL);
            ''')
            for table,column,definition in [('harness_runs','active_stage','TEXT'),('harness_runs','attempt','INTEGER NOT NULL DEFAULT 0'),('harness_stages','attempt','INTEGER NOT NULL DEFAULT 0')]:
                if column not in {row['name'] for row in c.execute(f'PRAGMA table_info({table})')}:
                    c.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
    @contextmanager
    def _db(self):
        c=sqlite3.connect(self.path,timeout=10); c.row_factory=sqlite3.Row
        try:
            c.execute('BEGIN IMMEDIATE'); yield c; c.commit()
        except BaseException:
            c.rollback(); raise
        finally: c.close()
    def _event(self,c,run_id,event):
        c.execute('INSERT INTO harness_events(run_id,payload) VALUES (?,?)',(run_id,json.dumps(event)))
    def create_run(self,request_id,input_revision,policy_version,idempotency_key):
        if policy_version != '1': raise ValueError('Unsupported policy version')
        with self._db() as c:
            old=c.execute('SELECT * FROM harness_runs WHERE idempotency_key=?',(idempotency_key,)).fetchone()
            if old:
                if (old['request_id'],old['input_revision'],old['policy_version']) != (request_id,input_revision,policy_version):
                    raise Conflict('Idempotency key belongs to different input')
                return dict(old)
            rid=uuid.uuid4().hex
            c.execute('INSERT INTO harness_runs(id,request_id,input_revision,policy_version,idempotency_key,revision,state,workspace) VALUES (?,?,?,?,?,0,?,?)',(rid,request_id,input_revision,policy_version,idempotency_key,'pending',self.path))
            self._event(c,rid,{'target':'pending'})
            return dict(c.execute('SELECT * FROM harness_runs WHERE id=?',(rid,)).fetchone())
    def get_run(self,run_id):
        with self._db() as c:
            r=c.execute('SELECT * FROM harness_runs WHERE id=?',(run_id,)).fetchone()
            if r is None: raise KeyError(run_id)
            return dict(r)
    def list_runs(self):
        with self._db() as c: return [dict(r) for r in c.execute('SELECT * FROM harness_runs ORDER BY rowid DESC')]
    def transition(self,run_id,expected_revision,target,event):
        with self._db() as c:
            r=c.execute('SELECT * FROM harness_runs WHERE id=?',(run_id,)).fetchone()
            if r is None: raise KeyError(run_id)
            if r['revision']!=expected_revision or target not in TRANSITIONS[r['state']]: raise Conflict('Stale revision or illegal transition')
            if target=='running':
                stage=event.get('stage')
                if r['active_stage'] and stage != r['active_stage']:
                    raise Conflict('Single-stage run cannot execute a different stage')
                if stage:
                    c.execute('UPDATE harness_runs SET active_stage=?,attempt=attempt+1 WHERE id=?',(stage,run_id))
            c.execute('UPDATE harness_runs SET state=?,revision=revision+1 WHERE id=?',(target,run_id))
            self._event(c,run_id,{'from':r['state'],'target':target,'revision':expected_revision+1,'event':event})
            return dict(c.execute('SELECT * FROM harness_runs WHERE id=?',(run_id,)).fetchone())
    def events(self,run_id):
        with self._db() as c: return [dict(r)|{'payload':json.loads(r['payload'])} for r in c.execute('SELECT * FROM harness_events WHERE run_id=? ORDER BY seq',(run_id,))]
    def stages(self,run_id):
        with self._db() as c: return [json.loads(r['payload']) for r in c.execute('SELECT payload FROM harness_stages WHERE run_id=? ORDER BY rowid',(run_id,))]
    def save_stage(self,run_id,expected_revision,record):
        with self._db() as c:
            r=c.execute('SELECT * FROM harness_runs WHERE id=?',(run_id,)).fetchone()
            if r['revision']!=expected_revision or r['state'] not in {'running','reviewing'}: raise Conflict('Late stage output')
            n=c.execute('SELECT COUNT(*) FROM harness_stages WHERE run_id=? AND stage=?',(run_id,record.stage)).fetchone()[0]
            if n>=3: raise Conflict('Two rework rounds exhausted')
            c.execute('INSERT INTO harness_stages(run_id,stage,round,payload,attempt) VALUES (?,?,?,?,?)',(run_id,record.stage,n,record.model_dump_json(),r['attempt']))
            self._event(c,run_id,{'stage':record.stage,'round':n,'artifact_revision':record.revision})
    def claim_workspace(self,run_id,workspace):
        with self._db() as c:
            try: c.execute('INSERT INTO harness_locks VALUES (?,?)',(str(Path(workspace).resolve()),run_id))
            except sqlite3.IntegrityError: raise Conflict('Workspace already executing')
    def release_workspace(self,run_id):
        with self._db() as c: c.execute('DELETE FROM harness_locks WHERE run_id=?',(run_id,))
    def claim_mutation(self,run_id,mutation_key):
        with self._db() as c:
            r=c.execute('SELECT state FROM harness_runs WHERE id=?',(run_id,)).fetchone()
            if r is None or r['state']=='cancelled': raise Conflict('Mutation run unavailable')
            try: c.execute('INSERT INTO harness_mutations VALUES (?,?,?,?)',(run_id,mutation_key,'unreconciled','{}'))
            except sqlite3.IntegrityError: return False
            self._event(c,run_id,{'mutation':mutation_key,'status':'unreconciled'}); return True
    def mutations(self,run_id):
        with self._db() as c: return [dict(r) for r in c.execute('SELECT * FROM harness_mutations WHERE run_id=?',(run_id,))]
    def resolve_mutation(self,run_id,mutation_key,receipt):
        if not receipt: raise ValueError('Reconciliation receipt required')
        with self._db() as c:
            cur=c.execute("UPDATE harness_mutations SET status='reconciled',receipt=? WHERE run_id=? AND mutation_key=? AND status='unreconciled'",(json.dumps(receipt),run_id,mutation_key))
            if cur.rowcount!=1: raise Conflict('Mutation not pending reconciliation')
            self._event(c,run_id,{'mutation':mutation_key,'receipt':receipt})
    def approve_stage(self,run_id,expected_revision,actor):
        """Actor must come from server identity resolution, never request JSON.

        Local demo identities are explicitly recorded as simulated. Production
        authentication and separation of author/releaser belong to API integration.
        """
        from .harness_models import StageRecord
        from .harness_policy import evaluate_stage
        if not actor.get('id') or actor.get('role') not in {'release_manager','admin'} or actor.get('identity_source') not in {'authenticated','demo_simulated'}:
            raise Conflict('Unauthorized approval identity')
        with self._db() as c:
            r=c.execute('SELECT * FROM harness_runs WHERE id=?',(run_id,)).fetchone()
            if r is None: raise KeyError(run_id)
            if r['revision']!=expected_revision or r['state']!='blocked': raise Conflict('Stale or unavailable approval')
            row=c.execute('SELECT rowid,payload,attempt,stage FROM harness_stages WHERE run_id=? ORDER BY rowid DESC LIMIT 1',(run_id,)).fetchone()
            if row is None or row['attempt']!=r['attempt'] or row['stage']!=r['active_stage']: raise Conflict('No current attempt snapshot')
            record=StageRecord.model_validate_json(row['payload'])
            record.human_approved=True
            record.approval_revision=record.revision
            record.approval_commit=record.commit
            decision=evaluate_stage(record,{})
            if any(m['status']=='unreconciled' for m in c.execute('SELECT status FROM harness_mutations WHERE run_id=?',(run_id,))):
                raise Conflict('Unreconciled mutation blocks approval')
            c.execute('UPDATE harness_stages SET payload=? WHERE rowid=?',(record.model_dump_json(),row['rowid']))
            target='completed' if decision.allowed else 'blocked'
            c.execute('UPDATE harness_runs SET state=?,revision=revision+1 WHERE id=?',(target,run_id))
            self._event(c,run_id,{'target':target,'revision':expected_revision+1,'actor':actor,'approval_revision':record.revision,'approval_commit':record.commit,'decision':json.loads(decision.model_dump_json())})
            return decision

    def all_mutations(self):
        with self._db() as c:
            return [dict(r) for r in c.execute('SELECT * FROM harness_mutations')]
