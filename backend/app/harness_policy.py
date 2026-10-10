"""Deterministic evidence scoring. Scores never override mandatory gates."""
import math
from .harness_models import PolicyDecision, ScoreComponent, StageRecord

WEIGHTS = {'acceptance': 30, 'verification': 30, 'review': 25, 'provenance': 15}
POLICY_VERSION = '1'
DEFAULT_THRESHOLD = 85


def evaluate_stage(stage: StageRecord, policy: dict) -> PolicyDecision:
    # Revalidate mutable nested structures before consuming any evidence.
    stage = StageRecord.model_validate(stage.model_dump())
    threshold = policy.get('threshold', DEFAULT_THRESHOLD)
    if isinstance(threshold, bool) or not isinstance(threshold, (float, int)) or not math.isfinite(threshold) or not 85 <= threshold <= 100:
        threshold = DEFAULT_THRESHOLD
    blockers = []
    components = {}
    def current(item):
        return item.revision == stage.revision and item.commit == stage.commit
    def receipt_valid(item):
        if item.exit_code is not None and item.exit_code != 0:
            return False
        return not item.command or (item.exit_code == 0 and item.duration_seconds is not None and all(arg.strip() for arg in item.command))
    def component(key, values, items):
        denominator = len(values)
        numerator = sum(values)
        fraction = numerator / denominator if denominator else 0
        components[key] = ScoreComponent(numerator=numerator, denominator=denominator,
            fraction=fraction, weight=WEIGHTS[key], points=fraction*WEIGHTS[key],
            sources=[x.source for x in items], timestamps=[x.timestamp for x in items])
    ids = [e.id for e in stage.evidence]
    if len(ids) != len(set(ids)):
        blockers.append('Duplicate evidence identifiers')
    manifest = policy.get('required_evidence_ids', [])
    if not isinstance(manifest, list) or any(not isinstance(x, str) or not x for x in manifest):
        blockers.append('Invalid required evidence manifest')
        manifest = []
    for evidence_id in set(stage.required_evidence_ids + manifest):
        matching = [e for e in stage.evidence if e.id == evidence_id]
        if len(matching) != 1 or matching[0].status != 'passed' or not current(matching[0]) or not receipt_valid(matching[0]):
            blockers.append(f'Missing or unsuccessful required evidence: {evidence_id}')
    for category in ('acceptance', 'verification'):
        items = [e for e in stage.evidence if e.category == category]
        component(category, [e.fraction if e.status == 'passed' and current(e) and receipt_valid(e) else 0 for e in items], items)
        if not items:
            blockers.append(f'Missing {category} evidence')
    for e in stage.evidence:
        if not receipt_valid(e):
            blockers.append(f'Invalid or unsuccessful execution receipt: {e.id}')
        if not current(e):
            blockers.append(f'Stale evidence: {e.id}')
        if e.required and e.status != 'passed':
            blockers.append(f'Required evidence {e.id}: {e.status}')
    roles = list(dict.fromkeys(stage.required_reviewers + [r.role for r in stage.reviews if r.required]))
    if not roles:
        blockers.append('Missing required reviewer configuration')
    review_values = []
    for role in roles:
        matching = [r for r in stage.reviews if r.role == role]
        valid = len(matching) == 1 and current(matching[0]) and matching[0].verdict == 'pass' and not matching[0].missing_checks
        review_values.append(1 if valid else 0)
        if not valid:
            blockers.append(f'Missing, stale or unsuccessful required review: {role}')
    for r in stage.reviews:
        if not current(r):
            blockers.append(f'Stale review: {r.role}')
        if r.verdict == 'block' or any(f.severity == 'critical' for f in r.findings):
            blockers.append(f'Blocking reviewer finding: {r.role}')
    component('review', review_values, stage.reviews)
    items = [e for e in stage.evidence if e.category == 'provenance']
    component('provenance', [e.fraction if e.status == 'passed' and current(e) and receipt_valid(e) else 0 for e in items], items)
    if not items:
        blockers.append('Missing provenance evidence')
    if not stage.authorized:
        blockers.append('Unauthorized action')
    if stage.human_approval_required and not (stage.human_approved and stage.approval_revision == stage.revision and stage.approval_commit == stage.commit):
        blockers.append('Missing current artifact-bound human approval')
    score = round(sum(c.points for c in components.values()), 6)
    if score < threshold:
        blockers.append(f'Evidence score {score:g} below threshold {threshold:g}')
    allowed = not blockers
    return PolicyDecision(score=score, threshold=threshold, allowed=allowed,
        components=components, blockers=list(dict.fromkeys(blockers)),
        next_action='advance' if allowed else ('rework' if any(r.verdict == 'rework' for r in stage.reviews) else 'human_review'))
