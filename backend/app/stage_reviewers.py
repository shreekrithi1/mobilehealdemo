"""Host-owned stage manifests and independent deterministic evidence reviews.

These reviews inspect receipts, not semantics or native runtime safety.
"""
from datetime import datetime, timezone
from .harness_models import ReviewResult, Finding

STAGES = ('requirements', 'design', 'code', 'test', 'incident', 'data', 'release')
ROLES = {'requirements': ['acceptance', 'ambiguity'], 'design': ['ux', 'acceptance'],
         'code': ['correctness', 'security'], 'test': ['coverage', 'receipt_integrity'],
         'incident': ['causal', 'replay'], 'data': ['quality', 'privacy'], 'release': ['policy', 'operability']}

def policies(revision=1):
    return {s: {'artifact_revision': revision, 'required_evidence_ids': [f'{s}.acceptance', f'{s}.verification', f'{s}.provenance'],
                'required_reviewers': ROLES[s], 'human_approval_required': s == 'release'} for s in STAGES}

def independent_review(role):
    def review(record):
        by_id = {e.id: e for e in record.evidence}
        missing = [i for i in record.required_evidence_ids if i not in by_id or by_id[i].status != 'passed'
                   or by_id[i].revision != record.revision or by_id[i].commit != record.commit]
        findings = [Finding(severity='info', message='Deterministic evidence scope only; semantic, device and security certification require separate review.')]
        if role in {'receipt_integrity', 'replay', 'operability'}:
            for item in record.evidence:
                if item.category == 'verification' and (not item.command or item.exit_code != 0 or item.duration_seconds is None):
                    missing.append(item.id + ':execution_receipt')
        elif role in {'security', 'privacy'}:
            from .harness_redaction import redact
            if any(redact(e.summary) != e.summary for e in record.evidence):
                missing.append('redacted_sensitive_content')
        elif role in {'acceptance', 'quality', 'ux'}:
            if not any(e.category == 'acceptance' and e.status == 'passed' for e in record.evidence):
                missing.append('acceptance_assertions')
        elif role in {'coverage', 'correctness'}:
            if len([e for e in record.evidence if e.category == 'verification' and e.command]) < 2:
                missing.append('contract_and_regression_receipts')
        elif role in {'policy', 'ambiguity', 'causal'}:
            if len(set(record.required_evidence_ids)) < 3:
                missing.append('complete_stage_manifest')
        return ReviewResult(role=role, verdict='block' if missing else 'pass', revision=record.revision,
                            commit=record.commit, source='deterministic receipt review', timestamp=datetime.now(timezone.utc),
                            missing_checks=missing, findings=findings)
    return review
