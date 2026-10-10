"""Read and approval APIs with server-owned identity and redacted responses."""
import hmac
import os
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from .harness_store import Conflict
from .harness_policy import evaluate_stage
from .harness_models import StageRecord
from .harness_redaction import redact
from .demomode import is_on

router = APIRouter(prefix='/api/harness', tags=['harness'])
class Revision(BaseModel):
    model_config = ConfigDict(extra='forbid')
    revision: int = Field(ge=0)

def resolve_actor(demo, authorization):
    if demo:
        return {'id': 'local-demo-human', 'role': 'release_manager', 'identity_source': 'demo_simulated'}
    raise HTTPException(403, 'Production identity provider and human role separation are not configured')

def context(request):
    return request.app.state.wf.harness

@router.get('/runs')
def runs(request: Request):
    return redact(context(request).store.list_runs())

@router.get('/policy')
def policy(request: Request):
    return {'version': '1', 'threshold': 85, 'stages': context(request).stage_policies,
            'limitations': ['Receipt reviews do not establish native execution safety', 'Audit is application-owned, not tamper-proof']}

@router.get('/runs/{run_id}')
def details(run_id: str, request: Request):
    store = context(request).store
    try:
        stages = store.stages(run_id)
        return redact({'run': store.get_run(run_id), 'stages': stages, 'events': store.events(run_id),
                       'mutations': store.mutations(run_id), 'decision': evaluate_stage(StageRecord.model_validate(stages[-1]),{}).model_dump(mode='json') if stages else None})
    except KeyError: raise HTTPException(404, 'Run not found')

@router.post('/runs/{run_id}/approve')
def approve(run_id: str, body: Revision, request: Request):
    wf = request.app.state.wf
    actor = resolve_actor(is_on(wf.settings), request.headers.get('authorization'))
    try:
        run = wf.harness.store.get_run(run_id)
        if run['input_revision'] != wf._harness_commit(): raise Conflict('Git revision changed; regenerate evidence')
        return wf.harness.store.approve_stage(run_id, body.revision, actor).model_dump(mode='json')
    except KeyError: raise HTTPException(404, 'Run not found')
    except Conflict as e: raise HTTPException(409, str(e))

@router.post('/runs/{run_id}/cancel')
def cancel(run_id: str, body: Revision, request: Request):
    wf = request.app.state.wf
    resolve_actor(is_on(wf.settings), request.headers.get('authorization'))
    try:
        if wf.harness.store.get_run(run_id)['revision'] != body.revision: raise Conflict('Stale revision')
        return wf.harness.cancel(run_id)
    except KeyError: raise HTTPException(404, 'Run not found')
    except Conflict as e: raise HTTPException(409, str(e))

@router.post('/requests/{cid}/prepare-release')
def prepare(cid: int, request: Request):
    wf = request.app.state.wf
    resolve_actor(is_on(wf.settings), request.headers.get('authorization'))
    try: return redact(wf.prepare_release(cid))
    except Exception as e: raise HTTPException(409, str(redact(str(e))))

from typing import Literal
class Intake(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source: Literal['change_request', 'firebase_crash', 'issue_email', 'jira_defect', 'ba_requirement']
    title: str = Field(min_length=1, max_length=200)
    spec_text: str = Field(min_length=1, max_length=16000)
    description: str = Field(default='', max_length=4000)
    idempotency_key: str = Field(min_length=1, max_length=120)

@router.post('/intake')
def intake(body: Intake, request: Request):
    wf = request.app.state.wf
    resolve_actor(is_on(wf.settings), request.headers.get('authorization'))
    with wf.db._lock:
        for cr in wf.list():
            old = wf.get(cr['id'])
            if old.get('intake', {}).get('idempotency_key') == body.idempotency_key:
                if old['intake']['source'] != body.source or old.get('spec_text') != body.spec_text:
                    raise HTTPException(409, 'Idempotency key belongs to a different intake')
                return redact({'request': old, 'connector_mode': 'mock', 'workflow': 'change_request'})
        try:
            cr = wf.create(body.title, body.description, body.spec_text, author='Local demo intake')
            cr['intake'] = {'source': body.source, 'connector_mode': 'mock', 'idempotency_key': body.idempotency_key,
                            'limitation': 'Supplied local requirement; crash and issue sources are categorized intake, not verified external incident evidence'}
            wf._save(cr)
            return redact({'request': cr, 'connector_mode': 'mock', 'workflow': 'change_request'})
        except Exception as e: raise HTTPException(400, str(redact(str(e))))
