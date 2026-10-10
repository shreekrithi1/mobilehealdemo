import threading
import time
from app.harness import Harness
from app.harness_models import StageRecord
from app.harness_store import HarnessStore, Conflict

def test_review_timeout(tmp_path):
 s=HarnessStore(tmp_path/'r.db'); r=s.create_run('r','c','1','k'); h=Harness(s,reviewer_timeout=.01)
 def review(record): time.sleep(.05)
 h.run_stage(r['id'],'code',lambda: StageRecord(stage='code',revision=1,commit='c',required_reviewers=['security']),[review])
 assert s.get_run(r['id'])['state']=='blocked'
 time.sleep(.06)
 assert s.get_run(r['id'])['state']=='blocked'

def test_cancel_and_restart(tmp_path):
 s=HarnessStore(tmp_path/'r.db'); r=s.create_run('r','c','1','k'); h=Harness(s)
 entered=threading.Event(); release=threading.Event(); errors=[]
 def producer():
  entered.set(); release.wait(); return StageRecord(stage='code',revision=1,commit='c')
 def execute():
  try: h.run_stage(r['id'],'code',producer,[])
  except Conflict as e: errors.append(e)
 t=threading.Thread(target=execute); t.start(); entered.wait(); h.cancel(r['id']); release.set(); t.join()
 assert errors and s.stages(r['id'])==[]
 r2=s.create_run('r2','c','1','k2'); s.transition(r2['id'],0,'running',{})
 assert h.reconcile()[0]['state']=='interrupted'

def test_workspace_exclusion_and_two_reworks(tmp_path):
 import pytest
 s=HarnessStore(tmp_path/'r.db'); r=s.create_run('r','c','1','k'); h=Harness(s)
 s.claim_workspace(r['id'],h.workspace)
 with pytest.raises(Conflict): h.run_stage(r['id'],'code',lambda: None,[])
 s.release_workspace(r['id'])
 for _ in range(3): h.run_stage(r['id'],'code',lambda: StageRecord(stage='code',revision=1,commit='c'),[])
 with pytest.raises(Conflict): h.run_stage(r['id'],'code',lambda: None,[])

def test_unreconciled_mutation_never_reexecutes(tmp_path):
 import pytest
 s=HarnessStore(tmp_path/'r.db'); r=s.create_run('r','c','1','k'); h=Harness(s)
 assert s.claim_mutation(r['id'],'merge')
 with pytest.raises(Conflict): h.run_stage(r['id'],'code',lambda: None,[])
 s.resolve_mutation(r['id'],'merge',{'commit':'verified'})
 assert not s.claim_mutation(r['id'],'merge')

def test_trusted_manifest_overrides_producer(tmp_path):
 s=HarnessStore(tmp_path/'r.db'); r=s.create_run('r','c','1','k')
 h=Harness(s,stage_policies={'code':{'required_reviewers':['security'],'required_evidence_ids':['native-build']}})
 result=h.run_stage(r['id'],'code',lambda: StageRecord(stage='code',revision=1,commit='c',human_approved=True),[])
 assert result.required_reviewers==['security']
 assert result.required_evidence_ids==['native-build']
 assert not result.human_approved
 assert s.get_run(r['id'])['state']=='blocked'

def test_reviewers_have_separate_frozen_inputs(tmp_path):
 from datetime import datetime, timezone
 from app.harness_models import ReviewResult
 s=HarnessStore(tmp_path/'r.db'); r=s.create_run('r','c','1','k')
 h=Harness(s,stage_policies={'code':{'required_reviewers':['a','b'],'required_evidence_ids':['check']}})
 barrier=threading.Barrier(2); observations=[]
 def review(role):
  def fn(record):
   if role=='a': record.commit='modified'
   barrier.wait(); observations.append((role,record.commit))
   return ReviewResult(role=role,verdict='pass',revision=1,commit='c',source=role,timestamp=datetime.now(timezone.utc))
  return fn
 h.run_stage(r['id'],'code',lambda: StageRecord(stage='code',revision=1,commit='c'),[review('a'),review('b')])
 assert ('b','c') in observations

def complete_record():
 from datetime import datetime, timezone
 from app.harness_models import EvidenceItem
 return StageRecord(stage='code',revision=1,commit='c',evidence=[EvidenceItem(id=k,category=k,status='passed',revision=1,commit='c',source='receipt',timestamp=datetime.now(timezone.utc)) for k in ['acceptance','verification','provenance']])

def successful_review(record):
 from datetime import datetime, timezone
 from app.harness_models import ReviewResult
 return ReviewResult(role='security',verdict='pass',revision=record.revision,commit=record.commit,source='independent',timestamp=datetime.now(timezone.utc))

def test_success_persists_joined_snapshot(tmp_path):
 s=HarnessStore(tmp_path/'r.db'); r=s.create_run('r','c','1','k')
 h=Harness(s,stage_policies={'code':{'required_reviewers':['security'],'required_evidence_ids':['acceptance','verification','provenance'],'human_approval_required':False}})
 record=h.run_stage(r['id'],'code',complete_record,[successful_review])
 assert s.get_run(r['id'])['state']=='completed'
 assert s.stages(r['id'])[0]['reviews'][0]['role']=='security'
 assert s.events(r['id'])[-1]['payload']['decision']['score']==100

def test_cancel_during_review_discards_late_results(tmp_path):
 s=HarnessStore(tmp_path/'r.db'); r=s.create_run('r','c','1','k'); h=Harness(s)
 entered=threading.Event(); release=threading.Event(); finished=threading.Event(); errors=[]
 def review(record):
  entered.set(); release.wait(); finished.set(); return successful_review(record)
 def execute():
  try: h.run_stage(r['id'],'code',complete_record,[review])
  except Conflict as e: errors.append(e)
 t=threading.Thread(target=execute); t.start(); assert entered.wait(1); h.cancel(r['id']); t.join(1)
 release.set(); assert finished.wait(1)
 assert errors and s.get_run(r['id'])['state']=='cancelled'
 assert s.stages(r['id'])[0]['reviews']==[]

def test_approval_bound_to_revision_and_no_producer_rerun(tmp_path):
 import pytest
 s=HarnessStore(tmp_path/'r.db'); r=s.create_run('r','c','1','k')
 h=Harness(s,stage_policies={'code':{'required_reviewers':['security'],'required_evidence_ids':['acceptance','verification','provenance'],'human_approval_required':True}})
 h.run_stage(r['id'],'code',complete_record,[successful_review]); current=s.get_run(r['id'])
 actor={'id':'human','role':'release_manager','identity_source':'demo_simulated'}
 with pytest.raises(Conflict): s.approve_stage(r['id'],current['revision']-1,actor)
 decision=s.approve_stage(r['id'],current['revision'],actor)
 assert decision.allowed and s.get_run(r['id'])['state']=='completed'
 assert len(s.stages(r['id']))==1
 assert s.events(r['id'])[-1]['payload']['actor']==actor

def test_producer_cannot_replace_artifact_identity(tmp_path):
 import pytest
 s=HarnessStore(tmp_path/'r.db'); r=s.create_run('r','c','1','k'); h=Harness(s)
 for record in [StageRecord(stage='code',revision=1,commit='other'),StageRecord(stage='code',revision=4,commit='c')]:
  with pytest.raises(Conflict): h.run_stage(r['id'],'code',lambda: record,[])
 assert s.stages(r['id'])==[]

def test_actual_mutation_callable_runs_once_and_failure_not_retried(tmp_path):
 import pytest
 from concurrent.futures import ThreadPoolExecutor
 s=HarnessStore(tmp_path/'r.db'); r=s.create_run('r','c','1','k'); h=Harness(s,mutation_operations={'merge','deploy'},stage_policies={'code':{'required_reviewers':['security'],'required_evidence_ids':['acceptance','verification','provenance'],'human_approval_required':False}}); calls=[]
 h.run_stage(r['id'],'code',complete_record,[successful_review])
 def mutation(): calls.append('merge'); return {'commit':'c'}
 def execute(_):
  try: return h.execute_mutation(r['id'],'merge',mutation)
  except Conflict: return None
 with ThreadPoolExecutor(2) as pool: list(pool.map(execute,range(2)))
 assert calls==['merge']
 def failure(): calls.append('failure'); raise RuntimeError('unknown external outcome')
 with pytest.raises(RuntimeError): h.execute_mutation(r['id'],'deploy',failure)
 with pytest.raises(Conflict): h.execute_mutation(r['id'],'deploy',failure)
 assert calls==['merge','failure']
 assert [m for m in s.mutations(r['id']) if m['mutation_key'].endswith('deploy')][0]['status']=='unreconciled'

def test_unknown_mutation_blocks_changed_operation(tmp_path):
 import pytest
 s=HarnessStore(tmp_path/'r.db'); r=s.create_run('r','c','1','k')
 h=Harness(s,mutation_operations={'merge','publish'},stage_policies={'code':{'required_reviewers':['security'],'required_evidence_ids':['acceptance','verification','provenance'],'human_approval_required':False}})
 h.run_stage(r['id'],'code',complete_record,[successful_review])
 def fail(): raise RuntimeError('unknown outcome')
 with pytest.raises(RuntimeError): h.execute_mutation(r['id'],'merge',fail)
 calls=[]
 with pytest.raises(Conflict): h.execute_mutation(r['id'],'publish',lambda: calls.append(1) or {'ok':True})
 with pytest.raises(Conflict): h.execute_mutation(r['id'],'arbitrary-new-key',lambda: calls.append(1) or {'ok':True})
 assert not calls

def test_stage_reuse_and_failed_attempt_reject_old_approval(tmp_path):
 import pytest
 s=HarnessStore(tmp_path/'r.db'); r=s.create_run('r','c','1','k')
 h=Harness(s,stage_policies={'code':{'required_reviewers':['security'],'required_evidence_ids':['acceptance','verification','provenance']}})
 h.run_stage(r['id'],'code',complete_record,[successful_review])
 before=s.get_run(r['id'])['revision']
 with pytest.raises(Conflict): h.run_stage(r['id'],'test',lambda: None,[])
 assert s.get_run(r['id'])['revision']==before
 def fail(): raise RuntimeError('producer failed')
 with pytest.raises(RuntimeError): h.run_stage(r['id'],'code',fail,[])
 current=s.get_run(r['id'])
 with pytest.raises(Conflict): s.approve_stage(r['id'],current['revision'],{'id':'human','role':'admin','identity_source':'demo_simulated'})

def test_failed_producers_consume_rework_budget(tmp_path):
 import pytest
 s=HarnessStore(tmp_path/'r.db'); r=s.create_run('r','c','1','k'); h=Harness(s)
 def fail(): raise RuntimeError('no artifact')
 for _ in range(3):
  with pytest.raises(RuntimeError): h.run_stage(r['id'],'code',fail,[])
 with pytest.raises(Conflict): h.run_stage(r['id'],'code',fail,[])
