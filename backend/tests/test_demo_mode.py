"""Demo mode: every integration simulated, isolated sample workspace, simulated PR + Confluence pages."""
import importlib
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(os.getenv("MOBILEHEAL_IN_CHECK") == "1", reason="not run inside workflow checks")
PROJECT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def c(tmp_path, monkeypatch):
    root = tmp_path / "demo-workspace"
    shutil.copytree(PROJECT, root, ignore=shutil.ignore_patterns(".git", ".mobileheal", ".venv", "*.db*", "__pycache__", "build"))
    (root / "backend" / "requirements.txt").write_text("name: required\nemail: required\n")
    subprocess.run(["git", "init", "-q"], cwd=root)
    for k, v in {"MOBILEHEAL_DEMO": "1", "MOBILEHEAL_ROOT": str(root), "MOBILEHEAL_SPEC": str(root / "backend" / "requirements.txt"),
                 "MOBILEHEAL_DB": str(tmp_path / "d.db"), "MOBILEHEAL_INTERVAL": "3600"}.items():
        monkeypatch.setenv(k, v)
    for v in ("ANTHROPIC_API_KEY", "GITHUB_TOKEN", "GITHUB_REPO", "GITLAB_TOKEN"):
        monkeypatch.delenv(v, raising=False)
    import app.main as m
    importlib.reload(m)
    with TestClient(m.app) as client:
        yield client


def test_all_integrations_work_in_demo(c):
    assert c.get("/api/demo-mode").json() == {"on": True, "forced": True}
    for name in ("github", "gitlab", "confluence", "jira", "zephyr"):
        assert c.post(f"/api/settings/test/{name}").status_code == 200, name
    st = c.post("/api/repo/sync").json()
    assert st["status"] == "synced" and st["analysis"]["stack"]["Hilt"]
    r = c.post("/api/cr", json={"title": "Rebrand", "spec_text": "name: required\nemail: required\nui.button_color = #079455\n",
                                "figma_url": "https://www.figma.com/design/AbC123/Profile?node-id=1-2"}).json()
    assert r["figma"]["fetched"] and r["figma"]["suggestions"]


def test_seed_and_full_pipeline(c):
    out = c.post("/api/demo-mode/seed").json()
    assert out["profiles"] == 6 and len(out["change_requests"]) == 3
    t0, candidate = time.time(), None
    while time.time() - t0 < 30:
        crs = c.get("/api/cr").json()
        assert not any(x["status"] == "merged" for x in crs)
        candidate = next((x for x in crs if x["status"] == "pr_open" and x["kind"] != "incident"), None)
        if candidate and any(x["kind"] == "incident" for x in crs):
            break
        time.sleep(0.25)
    assert candidate and any(x["kind"] == "incident" for x in crs), crs
    cid = candidate["id"]
    assert c.post("/api/delivery-mode", json={"mode": "manual"}).status_code == 200
    assert c.post(f"/api/cr/{cid}/merge").status_code == 409
    for case in c.get(f"/api/cr/{cid}/tests").json()["cases"]:
        assert c.post(f"/api/tests/{case['id']}/runs", json={"cr_id": cid, "status": "passed", "steps": []}).status_code == 201
    assert c.post(f"/api/cr/{cid}/test", json={"passed": True, "notes": "Demo generated rules cases passed"}).status_code == 200
    for reviewer in ("Demo reviewer one", "Demo reviewer two"):
        assert c.post(f"/api/cr/{cid}/review", json={"reviewer": reviewer, "state": "approved", "body": "Local generated rules reviewed"}).status_code == 200
    prepared = c.post(f"/api/harness/requests/{cid}/prepare-release")
    assert prepared.status_code == 200, prepared.text
    run_id = prepared.json()["harness_runs"]["release"]
    run = c.get(f"/api/harness/runs/{run_id}").json()["run"]
    approved = c.post(f"/api/harness/runs/{run_id}/approve", json={"revision": run["revision"]})
    assert approved.status_code == 200 and approved.json()["allowed"], approved.text
    merged = c.post(f"/api/cr/{cid}/merge")
    assert merged.status_code == 200, merged.text
    full = c.get(f"/api/cr/{cid}").json()
    assert full["pr"]["github_url"].startswith("/demo/github/")
    assert c.get(full["pr"]["github_url"]).status_code == 200
    assert c.get(full["confluence"]["url"]).status_code == 200
    assert c.get("/api/data-health").json()["open"] > 0
    assert c.post("/api/demo-mode/reset").json()["ok"] and c.get("/api/cr").json() == []
