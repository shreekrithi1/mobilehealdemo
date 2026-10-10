from app.stage_reviewers import policies, independent_review
from app.harness_models import StageRecord

def test_all_stages_have_trusted_manifests():
    assert set(policies(2)) == {'requirements','design','code','test','incident','data','release'}
    assert all(p['required_evidence_ids'] and p['required_reviewers'] for p in policies(2).values())

def test_missing_native_evidence_cannot_review_pass():
    r = StageRecord(stage='release', revision=1, commit='abc', required_evidence_ids=['native'])
    assert independent_review('safety')(r).verdict == 'block'

from test_workflow import wf, wait_status

import os
import pytest

@pytest.mark.skipif(os.getenv('MOBILEHEAL_IN_CHECK') == '1', reason='not recursively run within workflow checks')
def test_demo_rules_release_requires_receipts_and_human(wf):
    c, root = wf
    assert c.post('/api/demo-mode', json={'on': True}).status_code == 200
    marker = root / 'untrusted-code-executed'
    (root / 'backend/tests/conftest.py').write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('unsafe')\n")
    (root / 'backend/tests/test_untrusted.py').write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('unsafe')\n")
    cr = c.post('/api/cr', json={'title': 'Harness phone collection', 'spec_text': 'name: required\nemail: required\nphone_number: required\n'}).json()
    cid = cr['id']
    assert c.post(f'/api/cr/{cid}/approve').status_code == 200
    cr = wait_status(c, cid, 'pr_open')
    for case in c.get(f'/api/cr/{cid}/tests').json()['cases']:
        c.post(f"/api/tests/{case['id']}/runs", json={'cr_id': cid, 'status': 'passed', 'steps': []})
    for reviewer in ('Demo reviewer one', 'Demo reviewer two'):
        assert c.post(f'/api/cr/{cid}/review', json={'state': 'approved', 'body': 'Local deterministic rules scope reviewed', 'reviewer': reviewer}).status_code == 200
    assert c.post(f'/api/cr/{cid}/merge').status_code == 409
    prepared = c.post(f'/api/harness/requests/{cid}/prepare-release')
    assert prepared.status_code == 200, prepared.text
    run_id = prepared.json()['harness_runs']['release']
    detail = c.get(f'/api/harness/runs/{run_id}').json()
    assert not detail['decision']['allowed']
    assert c.post(f'/api/harness/runs/{run_id}/approve', json={'revision': detail['run']['revision'], 'actor': 'spoof'}).status_code == 422
    approved = c.post(f'/api/harness/runs/{run_id}/approve', json={'revision': detail['run']['revision']})
    assert approved.status_code == 200 and approved.json()['allowed'], approved.text
    assert not marker.exists(), 'Workspace test/conftest must never execute'
    workflow = c.app.state.wf
    original_checkout = workflow.git._on_base
    def claimed_checkout():
        assert any(m['status'] == 'unreconciled' for m in workflow.harness.store.mutations(run_id))
        with workflow.harness.store._db() as db:
            assert db.execute('SELECT run_id FROM harness_locks WHERE run_id=?', (run_id,)).fetchone()
        return original_checkout()
    workflow.git._on_base = claimed_checkout
    merged = c.post(f'/api/cr/{cid}/merge')
    assert merged.status_code == 200, merged.text
    assert c.post(f'/api/cr/{cid}/revert').status_code == 409
    assert c.get(f'/api/harness/runs/{run_id}').json()['mutations'][0]['status'] == 'reconciled'

def test_known_synthetic_crash_replay_has_real_source_bound_receipts(tmp_path):
    from types import SimpleNamespace
    from app.healer import Healer
    from app.demo import ORIGINALS
    from app.patcher import patch_source
    original = ORIGINALS['backend/app/features/greeting.py']
    intermediate = patch_source(original, 5, 'AttributeError', "'NoneType' object has no attribute 'split'")[0]
    repaired = patch_source(intermediate, 5, 'IndexError', 'list index out of range')[0]
    healer = Healer.__new__(Healer)
    healer.root = tmp_path
    healer.wf = SimpleNamespace(_harness_commit=lambda: 'synthetic-test-commit')
    inc = {'incident': {'file': 'backend/app/features/greeting.py', 'function': 'make_greeting'},
           'base_files': {'backend/app/features/greeting.py': original},
           'files': [{'path': 'backend/app/features/greeting.py', 'content': repaired}]}
    receipts = healer.trusted_greeting_receipts(inc)
    assert len(receipts) == 2 and all(r['exit_code'] == 0 and r['command'] and r['duration_seconds'] > 0 for r in receipts)
    inc['files'][0]['content'] += '\nraise RuntimeError("untrusted")\n'
    with pytest.raises(ValueError): healer.trusted_greeting_receipts(inc)

from test_healer import env, wait

@pytest.mark.skipif(os.getenv('MOBILEHEAL_IN_CHECK') == '1', reason='not recursively run within workflow checks')
def test_known_crash_capture_fix_human_merge_repairs_live_api(env):
    import importlib
    from app.features import greeting
    importlib.reload(greeting)
    c, root = env
    assert c.post('/api/demo-mode', json={'on': True}).status_code == 200
    pid = c.post('/api/profiles', json={'email': 'synthetic@example.test'}).json()['id']
    crashed = c.get(f'/api/profiles/{pid}/greeting')
    assert crashed.status_code == 500
    inc = c.get('/api/cr').json()[0]
    inc = wait(c, inc['id'], {'pr_open', 'needs_engineer'})
    assert inc['status'] == 'pr_open', inc.get('coding_log')
    cid = inc['id']
    for reviewer in ('Simulated crash reviewer one', 'Simulated crash reviewer two'):
        assert c.post(f'/api/cr/{cid}/review', json={'state': 'approved', 'reviewer': reviewer, 'body': 'Canonical synthetic repair reviewed'}).status_code == 200
    assert c.post(f'/api/cr/{cid}/test', json={'notes': 'Canonical replay reviewed', 'passed': True}).status_code == 200
    prepared = c.post(f'/api/harness/requests/{cid}/prepare-release')
    assert prepared.status_code == 200, prepared.text
    rid = prepared.json()['harness_runs']['release']
    detail = c.get(f'/api/harness/runs/{rid}').json()
    approval = c.post(f'/api/harness/runs/{rid}/approve', json={'revision': detail['run']['revision']})
    assert approval.status_code == 200 and approval.json()['allowed'], approval.text
    merged = c.post(f'/api/cr/{cid}/merge')
    assert merged.status_code == 200, merged.text
    assert c.get(f'/api/profiles/{pid}/greeting').status_code == 200
    importlib.reload(greeting)
