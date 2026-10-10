"""Bounded independent review joins with durable cancellation boundaries."""
import queue
import threading
import time
from pathlib import Path
from .harness_models import StageRecord, ReviewResult
from .harness_policy import evaluate_stage
from .harness_store import Conflict

class Harness:
    def __init__(self,store,workspace=None,reviewer_timeout=120,stage_policies=None,mutation_operations=None):
        self.store=store
        self.mutation_operations=frozenset(mutation_operations or {'merge'})
        import copy
        self.stage_policies=copy.deepcopy(stage_policies or {})
        self.workspace=str(Path(workspace or Path(store.path).parent).resolve())
        self.reviewer_timeout=min(float(reviewer_timeout),120)
        if self.reviewer_timeout<=0: raise ValueError('Positive review deadline required')
    def cancel(self,run_id):
        for _ in range(10):
            r=self.store.get_run(run_id)
            if r['state']=='cancelled': return r
            try: return self.store.transition(run_id,r['revision'],'cancelled',{'reason':'user cancellation'})
            except Conflict:
                if r['state']=='completed': raise
        raise Conflict('Concurrent cancellation conflict')
    def reconcile(self):
        recovered=[]
        for r in self.store.list_runs():
            if r['state'] in {'running','reviewing'}:
                recovered.append(self.store.transition(r['id'],r['revision'],'interrupted',{'reason':'execution interrupted; mutations require receipt reconciliation'}))
                self.store.release_workspace(r['id'])
        return recovered
    def run_stage(self,run_id,stage,producer,reviewers):
        self.store.claim_workspace(run_id,self.workspace)
        try:
            r=self.store.get_run(run_id)
            if r['active_stage'] and r['active_stage']!=stage: raise Conflict('Single-stage run cannot be reused')
            if r['attempt']>=3: raise Conflict('Two rework rounds exhausted')
            if any(m['status']=='unreconciled' for m in self.store.all_mutations()): raise Conflict('Unreconciled mutation blocks execution')
            r=self.store.transition(run_id,r['revision'],'running',{'stage':stage})
            record=StageRecord.model_validate(producer())
            trusted=self.stage_policies.get(stage,{})
            expected_artifact_revision=trusted.get('artifact_revision',1)
            if (record.stage!=stage or record.policy_version!=r['policy_version']
                    or record.commit!=r['input_revision'] or record.revision!=expected_artifact_revision):
                raise Conflict('Producer returned different stage, policy or artifact identity')
            # Producer-authored reviews and approvals cannot grant gate permission.
            record.reviews=[]; record.human_approved=False; record.approval_revision=None; record.approval_commit=None
            trusted=self.stage_policies.get(stage,{})
            record.required_reviewers=list(trusted.get('required_reviewers',[]))
            record.required_evidence_ids=list(trusted.get('required_evidence_ids',[]))
            record.human_approval_required=bool(trusted.get('human_approval_required',True))
            record.authorized=bool(trusted) and bool(record.required_reviewers) and bool(record.required_evidence_ids)
            self.store.save_stage(run_id,r['revision'],record)
            r=self.store.transition(run_id,r['revision'],'reviewing',{'stage':stage})
            frozen=record.model_dump_json(); results=queue.Queue()
            def review(index,fn):
                try: results.put((index,ReviewResult.model_validate(fn(StageRecord.model_validate_json(frozen)))))
                except Exception: results.put((index,None))
            for index,fn in enumerate(reviewers):
                threading.Thread(target=review,args=(index,fn),daemon=True).start()
            deadline=time.monotonic()+self.reviewer_timeout; seen=set()
            while len(seen)<len(reviewers):
                if self.store.get_run(run_id)['state']=='cancelled': raise Conflict('Cancelled review join')
                remaining=deadline-time.monotonic()
                if remaining<=0: break
                try: index,result=results.get(timeout=min(remaining,.05))
                except queue.Empty: continue
                seen.add(index)
                if result is not None: record.reviews.append(result)
            decision=evaluate_stage(record,{})
            complete=decision.allowed and len(seen)==len(reviewers) and len(record.reviews)==len(reviewers)
            # The final snapshot is committed together with the transition's CAS.
            self._finish(run_id,r,record,'completed' if complete else 'blocked',decision)
            return record
        except Exception:
            current=self.store.get_run(run_id)
            if current['state'] in {'running','reviewing'}:
                try: self.store.transition(run_id,current['revision'],'blocked',{'reason':'execution failed'})
                except Conflict: pass
            raise
        finally: self.store.release_workspace(run_id)
    def _finish(self,run_id,r,record,target,decision):
        # Single SQLite transaction prevents cancellation between final evidence and state.
        import json
        with self.store._db() as c:
            current=c.execute('SELECT * FROM harness_runs WHERE id=?',(run_id,)).fetchone()
            if current['revision']!=r['revision'] or current['state']!='reviewing': raise Conflict('Late review output')
            row=c.execute('SELECT MAX(round) FROM harness_stages WHERE run_id=? AND stage=?',(run_id,record.stage)).fetchone()[0]
            c.execute('UPDATE harness_stages SET payload=? WHERE run_id=? AND stage=? AND round=?',(record.model_dump_json(),run_id,record.stage,row))
            c.execute('UPDATE harness_runs SET state=?, revision=revision+1 WHERE id=?',(target,run_id))
            self.store._event(c,run_id,{'target':target,'revision':r['revision']+1,'decision':json.loads(decision.model_dump_json())})
    def execute_mutation(self,run_id,operation,mutation):
        """Execute a gated consequential mutation once; ambiguity stays unreconciled.

        The trusted operation allowlist determines canonical mutation identities. Callable must
        use the bounded tool executor and return an inspectable receipt dictionary.
        """
        if operation not in self.mutation_operations: raise Conflict('Operation is not allowlisted')
        self.store.claim_workspace(run_id,self.workspace)
        try:
            if any(m['status']=='unreconciled' for m in self.store.all_mutations()):
                raise Conflict('Unreconciled mutation blocks all further mutations')
            r=self.store.get_run(run_id)
            records=self.store.stages(run_id)
            if r['state']!='completed' or not records or not evaluate_stage(StageRecord.model_validate(records[-1]),{}).allowed:
                raise Conflict('Mutation requires a passed current stage')
            mutation_key=f'{self.workspace}:{records[-1]["commit"]}:{operation}'
            if not self.store.claim_mutation(run_id,mutation_key):
                raise Conflict('Mutation already claimed; reconcile instead of retrying')
            receipt=mutation()
            if not isinstance(receipt,dict) or not receipt:
                raise Conflict('Mutation outcome lacks reconciliation receipt')
            self.store.resolve_mutation(run_id,mutation_key,receipt)
            return receipt
        finally:
            self.store.release_workspace(run_id)
