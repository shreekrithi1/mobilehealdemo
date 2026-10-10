# Threat model

This document describes threats and required controls. A control is only demonstrated when the verification record identifies its executed test or observed behavior.

| Boundary / threat | Required control | Failure outcome |
|---|---|---|
| Request, email, issue or repository contains instructions to bypass policy | Treat content as data; trusted graph/tool registry owns execution | Reject unauthorized action |
| Producer invents tests or drops a required receipt | Trusted check manifest, executed receipt integrity and current revision binding | Block |
| Reviewer output malformed, missing, late or contradictory | Schema validation, deadline, required-role join and hard blockers | Block / rework |
| Traversal or symlink escapes workspace | Resolved-path containment and source path allowlist | Deny write |
| Shell command injection | Fixed executable plus structured allowlisted arguments; shell disabled | Deny tool |
| Credential or personal data leaves logs/provider boundary | Redaction before logging/call; synthetic local data | Reject/redact |
| Forged or stale approval | Authenticated role, exact revision/commit, separation of author and releaser | Reject approval |
| Duplicate request or retry after unknown mutation | Unique idempotency, workspace lock, recorded mutation receipt and reconciliation | Block duplicate |
| Agent modifies guardrails or credentials | Protected paths and trusted policy configuration | Deny |
| Shared-host tool exceeds budget | Process-group timeout/cancellation/output limits plus deployment isolation | Terminate / block |

Residual risks: deterministic review is limited to implemented checks; separate model executions are not proof of independent reasoning; evidence scores are not calibrated probabilities; application audit records are not tamper-proof storage; local process controls are not an operating-system sandbox. Production worker isolation, OIDC, tenant boundaries and connector permission enforcement require target-environment validation.
