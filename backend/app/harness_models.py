"""Versioned, closed contracts for artifact-bound evidence and gate decisions."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', validate_assignment=True)


class EvidenceItem(Contract):
    id: str = Field(min_length=1)
    category: Literal['acceptance', 'verification', 'provenance']
    status: Literal['passed', 'failed', 'skipped', 'unavailable', 'missing']
    required: bool = True
    revision: int = Field(ge=0)
    commit: str = Field(min_length=1)
    source: str = Field(min_length=1)
    timestamp: datetime
    fraction: float = Field(default=1, ge=0, le=1, allow_inf_nan=False)
    summary: str = ''
    command: list[str] = Field(default_factory=list)
    exit_code: int | None = None
    duration_seconds: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    artifacts: list[str] = Field(default_factory=list)


class Finding(Contract):
    severity: Literal['info', 'warning', 'critical']
    message: str
    evidence_ids: list[str] = Field(default_factory=list)


class ReviewResult(Contract):
    role: str = Field(min_length=1)
    verdict: Literal['pass', 'rework', 'block']
    required: bool = True
    revision: int = Field(ge=0)
    commit: str = Field(min_length=1)
    source: str = Field(min_length=1)
    timestamp: datetime
    findings: list[Finding] = Field(default_factory=list)
    missing_checks: list[str] = Field(default_factory=list)


class StageRecord(Contract):
    stage: str = Field(min_length=1)
    revision: int = Field(ge=0)
    commit: str = Field(min_length=1)
    policy_version: Literal['1'] = '1'
    evidence: list[EvidenceItem] = Field(default_factory=list)
    reviews: list[ReviewResult] = Field(default_factory=list)
    required_evidence_ids: list[str] = Field(default_factory=list)
    required_reviewers: list[str] = Field(default_factory=list)
    human_approval_required: bool = False
    human_approved: bool = False
    approval_revision: int | None = None
    approval_commit: str | None = None
    authorized: bool = True


class ScoreComponent(Contract):
    numerator: float
    denominator: int
    fraction: float = Field(ge=0, le=1, allow_inf_nan=False)
    weight: int
    points: float
    sources: list[str] = Field(default_factory=list)
    timestamps: list[datetime] = Field(default_factory=list)


class PolicyDecision(Contract):
    policy_version: Literal['1'] = '1'
    score: float = Field(ge=0, le=100, allow_inf_nan=False)
    threshold: float
    allowed: bool
    components: dict[str, ScoreComponent]
    blockers: list[str]
    next_action: Literal['advance', 'rework', 'human_review']
