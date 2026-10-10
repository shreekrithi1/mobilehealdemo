# Verification record

Verified locally on 10 October 2026 on macOS with Python 3.12. This record distinguishes working local capabilities from production deployment design.

## Current product verification

`bash scripts/verify-product.sh` completed: **90 passed, one existing Starlette/httpx deprecation warning, 16.07 seconds**. The script writes `.mobileheal/product-verification.xml` and exits nonzero on a failure. Covered suites: evidence policy, durable store, execution, tools, redaction, workflow/API integration, rules contract, security, data health, flow control and seeded demo.

The integration journeys use temporary databases and Git workspaces:

- Rules requirement → design → generated local branch → saved test results → two simulated human reviews → actual fixed-command contract/regression receipts → release evidence → artifact-bound simulated human approval → local merge.
- Actual HTTP missing-name failure → captured incident → deterministic canonical repair → human review → source-bound reproduction/replay/valid-input receipts → current release approval → merge → the same live HTTP request returns 200.
- Required stage manifests, unavailable native execution, gate bypass rejection, source-bound replay, production identity fail-closed, poisoned workspace tests and checkout-under-mutation-claim assertions.

The focused inherited Firebase/enterprise/review group completed **35 passed, one warning, 67.55 seconds** before the final execution hardening. These tests preserve negative override and human/production release gates. Independent review also executed **2 read-only scope tests**; OAuth scope assertions match Google's `jobs.query` contract. The final bounded affected batch passed **90 tests, one warning,28.32 seconds**, including final import-mode/redaction fixes and legacy review/integration checks. The final migrated flow-control/demo files also passed independently: **3 passed,11.46 seconds**; they are now part of the required 90-test command.

## Browser and artifact evidence

- Refreshed application reviewed across 15 desktop and 12 mobile views; mobile dismiss/focus, dark primary contrast and local-demo wording were corrected after independent review.
- Workflow studio source selection, pass/rework routing, pause/replay/static state and keyboard scroll region were reviewed. At viewport 390, document width 390: no horizontal page overflow. Diagram and connector data are labeled sample/mock.
- Live control-center browser acceptance created a labeled BA request, navigated to the request, rendered actual requirements/design stage records, confidence components and reviewer findings, and switched audience views. A live request’s **Run verification** action recorded successful code/test/data receipts and correctly blocked release at 45/100 for missing acceptance/reviews/human approval. Its mobile document width also equals viewport 390. Production actions are visibly unavailable.
- Codelab rebuilt 14 lessons. Setup at `#1` contains exactly `bash run-tutorial.sh` and `bash run-application.sh`. Merge/crash lessons include current release verification and simulated approval. Actual screenshots are included.
- Five editable pitch slides exported and inspected; package/layout/font checks and first-party re-import passed. `pitch/build/validation-revised.json` records this. Native PowerPoint was not independently tested. PDF export is unavailable due the bundled Helvetica resolver.
- Launcher isolation unit test passed. Shell syntax, inline/external JavaScript syntax, Python compilation and Git whitespace checks passed.

## Launcher verification

The shared launcher was exercised with Python 3.12 on ports 8020/8082: fresh environment creation, locked dependency installation, application/backend and tutorial readiness, credential-free demo mode, Ctrl+C cleanup and released ports. Separate wrappers select tutorial or application. Browser auto-opening and Linux/WSL execution were not exercised.

## Historical inherited suite

The earlier full inherited suite was interrupted after approximately ten minutes at **58 passed and 22 failed**. It never completed. Focused investigation corrected obsolete expectations that bypassed review/release gates and restored documented read-only Firebase scopes. The entire inherited suite has not been re-certified; the required product suite above is a distinct test set.

## Limits and release prerequisites

- Live connectors and model-provider accounts are unconfigured; intake uses labeled mocks. Human identities are simulated locally. No public deployment or app-store release occurs.
- Reviews are deterministic evidence inspections, not semantic correctness or security certification. Requirements/design use non-execution inspection. Confidence is evidence coverage, not predictive accuracy.
- Trusted Python exceptions execute only application-owned fixed assertions over validated rules or exact canonical demo source; arbitrary repository tests, generated Python and mutable package imports are unavailable. Process groups are not an OS sandbox.
- Native builds/device runs require an isolated runtime and SDK/device evidence; Android Firebase configuration was excluded.
- Rollback fails closed until its policy, evidence and mutation reconciliation are configured. SQLite is local durable state, not a multi-node production adapter. Startup reconciliation requires stopped workers.
- Production requires authenticated roles/separation, isolated workers, durable queue/database/artifact storage, live integration validation, capacity tests and backup/rollback drills. See PRODUCTION.md and THREAT-MODEL.md.
