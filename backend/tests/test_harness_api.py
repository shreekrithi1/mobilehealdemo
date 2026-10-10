import pytest
from fastapi import HTTPException
from app.harness_api import resolve_actor

def test_production_identity_fails_closed(monkeypatch):
    monkeypatch.delenv('MOBILEHEAL_HARNESS_TOKEN', raising=False)
    with pytest.raises(HTTPException): resolve_actor(False, None)

def test_demo_identity_is_explicitly_simulated():
    assert resolve_actor(True, None)['identity_source'] == 'demo_simulated'
