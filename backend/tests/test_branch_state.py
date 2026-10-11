import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from app.db import Database
from app.workflow import Workflow
from app.main import app

ANDROID = 'android/app/src/main/java/com/mobileheal/app/MainActivity.kt'

@pytest.fixture
def workspace(tmp_path, monkeypatch):
    root = tmp_path / 'workspace'
    (root / 'backend').mkdir(parents=True)
    source = root / ANDROID
    source.parent.mkdir(parents=True)
    source.write_text('original source')
    (root / 'backend/requirements.txt').write_text('name: required\n')
    db = Database(tmp_path / 'state.db')
    workflow = Workflow(db, None, root)
    monkeypatch.setattr(app.state, 'wf', workflow, raising=False)
    yield workflow, root, TestClient(app)
    db._conn.close()


def store(workflow, cr):
    workflow.db._conn.execute('INSERT INTO change_requests (id, data) VALUES (?, ?)', (cr['id'], json.dumps(cr)))


def test_incident_reports_source_changed_since_fix(workspace):
    workflow, root, client = workspace
    store(workflow, {'id': 1, 'kind': 'incident', 'status': 'pr_open', 'base_files': {ANDROID: 'original source'}})
    assert client.get('/api/cr/1').json()['branch_state'] == {'up_to_date': True, 'changed_files': []}
    (root / ANDROID).write_text('new source')
    assert client.get('/api/cr/1').json()['branch_state'] == {'up_to_date': False, 'changed_files': [ANDROID]}
    assert workflow._stale(workflow.get(1))
    # Computed state must not become a saved snapshot.
    assert 'branch_state' not in workflow.get(1)


def test_removed_incident_source_is_stale(workspace):
    workflow, root, client = workspace
    store(workflow, {'id': 2, 'kind': 'incident', 'status': 'pr_open', 'base_files': {ANDROID: 'original source'}})
    (root / ANDROID).unlink()
    assert client.get('/api/cr/2').json()['branch_state']['changed_files'] == [ANDROID]


def test_requirement_reports_changed_live_rules(workspace):
    workflow, root, client = workspace
    store(workflow, {'id': 3, 'kind': 'change', 'status': 'pr_open', 'base_spec': 'name: required\n'})
    assert client.get('/api/cr/3').json()['branch_state']['up_to_date']
    (root / 'backend/requirements.txt').write_text('name: optional\n')
    assert client.get('/api/cr/3').json()['branch_state'] == {'up_to_date': False, 'changed_files': ['backend/requirements.txt']}
