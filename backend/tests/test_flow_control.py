"""Stop, revert and restart a delivery workflow."""
import os
import time

import pytest

from tests.test_figsync import c, wait, SPEC  # noqa: F401  (demo fixture + helpers)

pytestmark = pytest.mark.skipif(os.getenv("MOBILEHEAL_IN_CHECK") == "1", reason="not run inside workflow checks")


def test_stop_restart_and_merge_with_human_release_then_block_rollback(c):
    c, root = c
    c.post("/api/delivery-mode", json={"mode": "manual"})
    cr = c.post("/api/cr", json={"title": "City", "description": "", "spec_text": SPEC + "city: optional\n"}).json()
    c.post(f"/api/cr/{cr['id']}/approve")
    st = c.post(f"/api/cr/{cr['id']}/stop").json()
    assert st["status"] == "stopped" and st["stopped_from"] in ("coding", "pr_open")
    time.sleep(3)                                            # the coding thread must not resurrect it
    assert c.get(f"/api/cr/{cr['id']}").json()["status"] == "stopped"
    assert c.post(f"/api/cr/{cr['id']}/stop").status_code == 409
    assert c.post(f"/api/cr/{cr['id']}/revert").status_code == 409   # nothing merged yet
    r = c.post(f"/api/cr/{cr['id']}/restart").json()
    assert r["status"] == "design_review" and r["restarts"] == 1 and "pr" not in r
    c.post(f"/api/cr/{cr['id']}/approve")
    cr = wait(c, cr["id"], {"pr_open"}, timeout=30)
    assert c.post(f"/api/cr/{cr['id']}/test", json={"passed": True, "override": True, "notes": "verified on device after restart"}).status_code == 409
    assert c.post(f"/api/cr/{cr['id']}/merge").status_code == 409
    for case in c.get(f"/api/cr/{cr['id']}/tests").json()["cases"]:
        assert c.post(f"/api/tests/{case['id']}/runs", json={"cr_id": cr['id'], "status": "passed", "steps": []}).status_code == 201
    assert c.post(f"/api/cr/{cr['id']}/test", json={"passed": True, "notes": "Local generated cases passed after restart"}).status_code == 200
    for reviewer in ("Demo reviewer one", "Demo reviewer two"):
        assert c.post(f"/api/cr/{cr['id']}/review", json={"reviewer": reviewer, "state": "approved", "body": "Restarted artifact reviewed"}).status_code == 200
    prepared = c.post(f"/api/harness/requests/{cr['id']}/prepare-release")
    assert prepared.status_code == 200, prepared.text
    run_id = prepared.json()["harness_runs"]["release"]
    run = c.get(f"/api/harness/runs/{run_id}").json()["run"]
    approved = c.post(f"/api/harness/runs/{run_id}/approve", json={"revision": run["revision"]})
    assert approved.status_code == 200 and approved.json()["allowed"], approved.text
    m = c.post(f"/api/cr/{cr['id']}/merge"); assert m.status_code == 200, m.text
    spec = root / "backend/requirements.txt"
    assert "city: optional" in spec.read_text()
    assert c.post(f"/api/cr/{cr['id']}/restart").status_code == 409            # live: revert first
    shipped = spec.read_text()
    rv = c.post(f"/api/cr/{cr['id']}/revert")
    assert rv.status_code == 409 and "Rollback is unavailable" in rv.json()["detail"]
    assert spec.read_text() == shipped
    assert c.get(f"/api/cr/{cr['id']}").json()["status"] == "merged"
    assert c.post(f"/api/cr/{cr['id']}/restart").status_code == 409
