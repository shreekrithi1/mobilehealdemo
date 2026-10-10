import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from pydantic import ValidationError
from app.harness_models import EvidenceItem, ReviewResult, StageRecord
from app.harness_policy import evaluate_stage


def stage():
    common = dict(revision=1, commit='abc', source='receipt', timestamp='2026-10-10T10:00:00Z')
    return StageRecord(stage='code', revision=1, commit='abc', required_reviewers=['security'],
        evidence=[EvidenceItem(id=c, category=c, status='passed', **common) for c in ['acceptance','verification','provenance']],
        reviews=[ReviewResult(role='security', verdict='pass', **common)])


def test_complete():
    d = evaluate_stage(stage(), {})
    assert d.score == 100 and d.allowed and not d.blockers
    assert [x.weight for x in d.components.values()] == [30,30,25,15]


def test_missing_review():
    s=stage(); s.reviews=[]
    d=evaluate_stage(s,{})
    assert d.score==75 and not d.allowed and d.blockers


@pytest.mark.parametrize('status',['failed','skipped','unavailable','missing'])
def test_required_evidence_blocks(status):
    s=stage(); s.evidence[1].status=status
    assert not evaluate_stage(s,{}).allowed


@pytest.mark.parametrize('field,value',[('commit','old'),('revision',0)])
def test_stale_evidence_blocks(field,value):
    s=stage(); setattr(s.evidence[0],field,value)
    assert not evaluate_stage(s,{}).allowed


def test_threshold_84():
    s=stage(); s.evidence[0].fraction=14/30
    d=evaluate_stage(s,{})
    assert d.score==84 and not d.allowed


@pytest.mark.parametrize('value',[-.1,1.1,float('nan'),float('inf')])
def test_invalid_fraction(value):
    with pytest.raises(ValidationError):
        EvidenceItem(id='x',category='acceptance',status='passed',revision=1,commit='a',source='x',timestamp='2026-10-10T00:00:00Z',fraction=value)


def test_strict_review():
    for change in [dict(verdict='maybe'),dict(extra=True)]:
        data=stage().reviews[0].model_dump(); data.update(change)
        with pytest.raises(ValidationError): ReviewResult(**data)


def test_fixed_weights_and_hard_gates():
    s=stage(); s.authorized=False
    d=evaluate_stage(s,{'weights':{'acceptance':100},'threshold':0})
    assert d.score==100 and not d.allowed
    s.authorized=True; s.human_approval_required=True
    assert not evaluate_stage(s,{}).allowed


def test_critical_and_stale_approval():
    s=stage(); s.reviews[0].findings=[dict(severity='critical',message='unsafe',evidence_ids=[])]
    assert not evaluate_stage(s,{}).allowed
    s=stage(); s.human_approval_required=True; s.human_approved=True; s.approval_revision=0; s.approval_commit='abc'
    assert not evaluate_stage(s,{}).allowed


def test_absent_components_zero():
    s=stage(); s.evidence=[]
    d=evaluate_stage(s,{})
    assert d.score==25 and not d.allowed


@pytest.mark.parametrize('change',[{'commit':'old'},{'revision':0},{'verdict':'rework'},{'missing_checks':['build']}])
def test_review_join_requires_current_complete_pass(change):
    s=stage()
    for field,value in change.items(): setattr(s.reviews[0],field,value)
    assert not evaluate_stage(s,{}).allowed


def test_duplicate_receipts_and_reviewers_block():
    s=stage(); s.evidence.append(s.evidence[0].model_copy())
    assert not evaluate_stage(s,{}).allowed
    s=stage(); s.reviews.append(s.reviews[0].model_copy())
    assert not evaluate_stage(s,{}).allowed


def test_current_human_approval_passes():
    s=stage(); s.human_approval_required=True; s.human_approved=True
    s.approval_revision=1; s.approval_commit='abc'
    assert evaluate_stage(s,{}).allowed


def test_higher_configured_threshold_is_honored():
    s=stage(); s.evidence[0].fraction=.9
    assert evaluate_stage(s,{}).allowed
    assert not evaluate_stage(s,{'threshold':99}).allowed


def test_trusted_manifest_blocks_disappeared_required_build():
    s=stage()
    s.required_evidence_ids=['acceptance','verification','provenance','native-build']
    assert not evaluate_stage(s,{}).allowed
    s.required_evidence_ids=[]
    assert not evaluate_stage(s,{'required_evidence_ids':['native-build']}).allowed


@pytest.mark.parametrize('exit_code,duration',[(1,1.0),(None,1.0),(0,None)])
def test_executed_command_requires_successful_complete_receipt(exit_code,duration):
    s=stage(); s.evidence[1].command=['pytest']; s.evidence[1].exit_code=exit_code
    s.evidence[1].duration_seconds=duration
    d=evaluate_stage(s,{})
    assert not d.allowed and d.components['verification'].points==0
