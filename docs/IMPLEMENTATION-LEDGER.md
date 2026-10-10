# Product implementation ledger

Approved scope: the local product, production deployment design, five-slide pitch deck, five-source animated workflow and full application refresh. The user approved execution with independent task reviewers. The spec and plan are in docs/superpowers/.

## Completed work and review

- Evidence policy: closed schemas, trusted manifests and deterministic confidence. Missing-check omission and nonzero command exit loopholes were fixed; independent scoped review approved. Initial focused run:28 passed.
- Durable harness: SQLite revisions, frozen independent reviews, bounded rework, stage-bound approval and canonical mutation receipts. Changed-key retry of an unknown mutation and stale-stage approval were fixed; review approved. Initial combined run:45 passed.
- Tool guardrails: named tools, path containment, bounded execution, unavailable isolation and redaction. Raw/compound JSON credentials and incomplete PEM leaks were fixed; review approved. Initial focused run:28 passed.
- Backend integration: requirements/design records, real supported verification receipts, stage-specific limited reviewers, explicit simulated human release approval, mock intake and production identity fail-closed. Arbitrary repository pytest/import execution was removed. Checkout occurs inside the locked claimed merge. Rollback fails closed. Independent scoped review:7 passed in 4.77 seconds; approved.
- UI and animation: desktop/mobile application refresh, control center, five starting sources, review/test rework, pause/replay/static view and keyboard scroll region. Mobile dismissal/focus, contrast, truthful demo wording and static-toggle state were corrected; independent review approved.
- Baseline repairs: documented read-only Firebase scopes and current human/release gates.35 focused tests passed; independent scope checks:2 passed. Stop/restart and seeded-demo tests were migrated without weakening negative gates; root verification:3 passed in 11.46 seconds; review approved.
- Documentation and deck: setup keeps exactly two separate shell commands. Merge/crash lessons show current evidence and approval. Production design, threat model, harness and guardrails describe real limits. Exactly five editable slides, all previews inspected; package/layout/font checks and re-import passed. PDF export was unavailable. Broad final review approved.

## Final verification

`bash scripts/verify-product.sh`: **90 passed, one existing Starlette/httpx warning,16.07 seconds**. Final bounded affected batch:90 passed in 28.32 seconds. These are overlapping test sets, not 180 unique tests. The earlier inherited full suite did not complete and is not certified green.

Both real API journeys passed: approved rules delivery to local merge, and captured canonical missing-name crash to reviewed repair, merge and successful live HTTP replay. Poisoned workspace tests were not executed; checkout ordering was asserted; blocked rollback left source unchanged.

Live browser acceptance created a labeled BA request, rendered actual requirements/design records, switched audience views and ran release verification. Code/test/data evidence passed while missing required acceptance/reviews/human approval correctly blocked release at 45/100. At 390 px, control-center and workflow document widths equal viewport width. Application review covered 15 desktop and 12 mobile views.

Launcher isolation unit test, shell/JavaScript syntax, Python compilation and Git whitespace checks passed. The fresh launcher installation/start/stop test is detailed in VERIFICATION.md. Runtime databases, credentials and environments remain excluded from version control.

## Implementation rulings

1. Run backend pytest with cwd `backend` (or `PYTHONPATH=backend`), correcting the original root-level import assumption. The wrong choice causes collection failures, not a product behavior change.
2. Use one durable run per stage, grouped under the workflow item, so failed new attempts cannot expose an older snapshot for approval. The wrong choice costs integration migration rather than relaxed gates.
3. Fail closed when a required OS isolation runtime is absent. Explicit host exceptions use only fixed Git operations or application-owned canonical Python assertions. Process groups cannot guarantee containment of detached children. The cost is unavailable arbitrary/native execution until a suitable adapter exists.

Production identity, isolated workers/native execution, live connectors, rollback verification, backup restoration and capacity remain deployment prerequisites. See PRODUCTION.md and VERIFICATION.md. Reviewed changes are ready for the user-authorized push.
