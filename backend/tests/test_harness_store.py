from concurrent.futures import ThreadPoolExecutor
import pytest
from app.harness_store import HarnessStore, Conflict

def test_idempotency_and_cas(tmp_path):
 s=HarnessStore(tmp_path/'runs.db'); r=s.create_run('r','c','1','k')
 assert s.create_run('r','c','1','k')['id']==r['id']
 with pytest.raises(Conflict): s.create_run('other','c','1','k')
 with pytest.raises(Conflict): s.transition(r['id'],0,'completed',{})
 def start(_):
  try: return s.transition(r['id'],0,'running',{})
  except Conflict: return None
 with ThreadPoolExecutor(2) as p: assert sum(x is not None for x in p.map(start,range(2)))==1
 assert len(s.events(r['id']))==2

def test_mutation_restart(tmp_path):
 s=HarnessStore(tmp_path/'r.db'); r=s.create_run('r','c','1','k')
 assert s.claim_mutation(r['id'],'merge')
 assert not HarnessStore(tmp_path/'r.db').claim_mutation(r['id'],'merge')

def test_mutation_key_deduplicates_concurrent_runs(tmp_path):
 s=HarnessStore(tmp_path/'r.db'); a=s.create_run('a','c','1','a'); b=s.create_run('b','c','1','b')
 with ThreadPoolExecutor(2) as pool:
  results=list(pool.map(lambda r: s.claim_mutation(r['id'],'workspace:commit:merge'),[a,b]))
 assert sum(results)==1
