# MobileHeal Product Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a verified local MobileHeal product with durable agent execution, evidence-backed review gates, understandable controls, deployment documentation and five editable pitch slides.

**Architecture:** Introduce focused harness, policy, evidence and tool modules beside the existing workflow. Preserve current local demo adapters, but route consequential stage transitions through a persisted gate that requires current evidence and human authorization. The portal exposes the same records used by enforcement.

**Tech Stack:** Existing Python 3.10+ / FastAPI / SQLite backend and HTML/CSS/JavaScript portal; pytest; stdlib process controls; JavaScript artifact-tool for editable PPTX.

**Spec:** `docs/superpowers/specs/2026-10-10-mobileheal-product-design.md`

## Global Constraints

- Preserve separate `bash run-tutorial.sh` and `bash run-application.sh` launch instructions and isolated demo workspace.
- No external credentials required for local mode; integrations and identities visibly simulated.
- Evidence confidence: acceptance coverage 30%, executed verification 30%, review completeness 25%, reproducibility/provenance 15%; threshold 85 plus all mandatory gates.
- Two rework rounds per stage; one transient-read retry; zero automatic retries for unreconciled mutations; reviewer timeout 120 seconds; tool timeout 300 seconds unless bounded native adapter override.
- Model responses and untrusted repository/request/tool content cannot change policy or grant permission.
- No public deployment or unsupported production-readiness claim. Record actual checks and unresolved limits.

## Review Focus

- Duplicate or concurrent requests must not execute the same mutation twice; test in Task 2.
- Evidence arriving after cancellation or artifact replacement must not advance a stage; test in Tasks 2 and 4.
- A skipped native check must appear unavailable and block when required; test in Tasks 1 and 5.
- Customer text that includes credentials or tool instructions must not leak secrets or expand permissions; test in Task 3.
- Multiple tabs or stale clients must not approve a newer revision using an old approval; test in Tasks 4 and 6.

## Task 1: Evidence contracts and deterministic policy

**Files:** Create `backend/app/harness_models.py`, `backend/app/harness_policy.py`; test `backend/tests/test_harness_policy.py`.

**Interfaces:** Pydantic models `EvidenceItem`, `ReviewResult`, `StageRecord`, `PolicyDecision` with forbidden extra fields; `evaluate_stage(stage: StageRecord, policy: dict) -> PolicyDecision`. Evidence carries status, required flag, revision, commit, source and timestamp. Decision carries score, component breakdown, blockers and next action.

- [ ] Write failing tests: complete evidence scores 100; missing review scores below 100 and blocks; failed required test blocks at any score; stale commit blocks; skipped required build blocks; unknown/invalid verdict is rejected; component fractions are bounded and use fixed weights 30/30/25/15; 84 blocks threshold advancement.
- [ ] Run `backend/.venv/bin/python -m pytest backend/tests/test_harness_policy.py -q`; confirm failures for missing implementation.
- [ ] Implement contracts and policy, version `1`, treating absent and skipped evidence as zero; no probabilistic wording.
- [ ] Re-run the same suite and require all pass.
- [ ] Commit contracts, policy and tests.

## Task 2: Durable harness and bounded stage orchestration

**Files:** Create `backend/app/harness_store.py`, `backend/app/harness.py`; test `backend/tests/test_harness_store.py`, `backend/tests/test_harness_execution.py`. Inspect existing `backend/app/db.py` before adding tables.

**Interfaces:** `HarnessStore.create_run(request_id: str, input_revision: str, policy_version: str, idempotency_key: str) -> dict`; `transition(run_id: str, expected_revision: int, target: str, event: dict) -> dict`; `Harness.run_stage(run_id: str, stage: str, producer: callable, reviewers: list[callable]) -> StageRecord`; `Harness.cancel(run_id: str) -> dict`; `Harness.reconcile() -> list[dict]`.

- [ ] Write failing tests for legal/illegal transitions, duplicate idempotency keys, concurrent compare-and-set updates, per-workspace exclusion, restart interruption, reviewer join with one missing or timed-out reviewer, cancellation and late output, two-round exhaustion and mutation reconciliation.
- [ ] Run the two focused suites; confirm intended failures.
- [ ] Add dedicated run/stage/event tables with unique idempotency constraint and append-only application audit events; no claim of tamper-proof storage. Implement persisted transitions and frozen reviewer snapshots using separate executions, bounded parallel join and cancellation.
- [ ] Re-run focused suites; require no duplicate mutation, no late advancement and no missing-review pass.
- [ ] Commit durable harness and tests.

## Task 3: Tool permissions, privacy and process lifetime

**Files:** Create `backend/app/harness_tools.py`, `backend/app/harness_redaction.py`; modify tool entry points in `backend/app/gitops.py`, `backend/app/android_agent.py`, `backend/app/ios_agent.py`, `backend/app/ai.py` after tracing current calls; test `backend/tests/test_harness_tools.py`, `backend/tests/test_harness_redaction.py`.

**Interfaces:** `ToolExecutor.execute(tool_name: str, arguments: dict, context: dict) -> EvidenceItem`; `resolve_allowed_path(root: Path, relative: str, allowed_paths: list[str]) -> Path`; `redact(value: object) -> object`. Registry entries define executable, structured arguments, permission, mutation flag, timeout and output cap.

- [ ] Write failing tests for traversal and symlink escapes, credential/Git-internal/policy writes, unknown tools, shell metacharacters, attempted instruction injection, secret and personal-data redaction, timeout process-tree cleanup, output truncation and forbidden external actions in demo mode.
- [ ] Run both suites; confirm failures.
- [ ] Implement path containment and explicit tool registry. Invoke argv without shell; enforce bounded execution, child-process termination and structured receipts. Redact before logging or model calls; preserve inspectable summaries rather than sensitive raw values.
- [ ] Route existing relevant tools through the executor without breaking fixed native build commands; classify unavailable SDKs as unavailable evidence.
- [ ] Re-run focused guardrail tests plus existing security tests and commit.

## Task 4: Integrate gates into delivery, incidents and data operations

**Files:** Modify `backend/app/workflow.py`, `backend/app/review.py`, `backend/app/healer.py`, `backend/app/watchdog.py`, `backend/app/council.py`; create `backend/app/stage_reviewers.py`; test `backend/tests/test_harness_workflows.py`.

**Interfaces:** `build_stage_evidence(workflow_item: dict, stage: str) -> StageRecord`; `review_stage(stage: StageRecord, role: str) -> ReviewResult`. Workflow items gain `harness_run_id` and `artifact_revision`. `approve_stage(run_id: str, revision: int, actor: dict) -> PolicyDecision` binds approval to evidence revision and commit.

- [ ] Trace and list every stage-advance/merge path before editing; cover manual and Autopilot callers.
- [ ] Write failing integration tests for requirements/design/code/test/incident/data/release reviewers; current-commit approvals; stale tab approvals; author self-release; failed test at merge; high score with critical blocker; changed artifact invalidation; data scan without mutation; crash replay failure; bypass attempts through Autopilot or settings.
- [ ] Run focused integration tests and confirm failures.
- [ ] Wire production stages to durable harness and stage-specific independent reviews. Maintain clearly labeled demo human actions. Remove unsupported council claims about affected users, privacy, tests or rollout where evidence is absent; expose unknowns explicitly. Enforce policy before Git merge or external action, not only in the UI.
- [ ] Run integration tests and existing review/healer/watchdog suites; investigate failures rather than weakening expectations. Commit.

## Task 5: Baseline failures and executable acceptance harness

**Files:** Create `scripts/verify-product.sh`, `backend/tests/test_product_journey.py`; modify existing files only as identified by failure investigation; update `docs/VERIFICATION.md` and create `docs/ACCEPTANCE.md`.

**Interfaces:** Verification script exits nonzero for required failures and emits machine-readable run metadata/report, command receipts and categorized unavailable integrations/native checks. Product journey test consumes the real API with isolated temporary workspace and database.

- [ ] Reproduce inherited failures in bounded groups with recorded commands, durations and results; classify code defect, obsolete behavior expectation or unavailable environment based on evidence.
- [ ] For each in-scope defect, add a failing regression test, implement the fix, then rerun the relevant group. Preserve negative-path coverage and do not count skips as passing mandatory checks.
- [ ] Write and run end-to-end API tests for requirement to local merge, crash to approved fix and replay, and data scan to reviewed recommendation. Include missing test, stale review, failed reproduction, duplicate mutation and exhausted budget cases.
- [ ] Implement `scripts/verify-product.sh` to run required suites and report accurate status. Run fresh launcher dependency installation and verify both separate launchers start/stop without orphaned servers.
- [ ] Commit fixes, acceptance harness and verification record. Any remaining required failure blocks the product readiness claim.

## Task 6: Product control center and audience-specific explanation

**Files:** Create `backend/app/harness_api.py`, `backend/app/static/agent-center.html`, `backend/app/static/agent-center.js`, `backend/app/static/agent-center.css`; modify `backend/app/main.py` and `backend/app/static/workflow.html`; test `backend/tests/test_harness_api.py`.

**Interfaces:** `GET /api/harness/runs`, `GET /api/harness/runs/{id}`, `GET /api/harness/policy`; `POST /api/harness/runs/{id}/approve` body revision and decision; `POST /api/harness/runs/{id}/cancel`. Responses use Task 1/2 records. Production-role enforcement fails closed; local demo actions labeled simulated.

- [ ] Write failing API tests for schema, unauthorized actions, stale revisions, approval identity and absence of secrets in evidence responses.
- [ ] Run tests, implement routers and plain-language UI, then rerun tests. Business view shows result, blockers and next action; developer view expands diff/test receipts; architect view expands policy and execution graph. All three show the same underlying state.
- [ ] Verify browser workflow on desktop and mobile; keyboard navigation, visible focus, expanded evidence, blocked actions, reviewer join, confidence components and revision-conflict recovery. Capture actual screenshots; fix layout/interaction issues.
- [ ] Commit UI/API and evidence screenshots.

## Task 7: Production deployment design and technical documentation

**Files:** Create `docs/PRODUCTION.md`, `docs/THREAT-MODEL.md`, `docs/AGENT-HARNESS.md`, `docs/GUARDRAILS.md`; update `README.md`, `codelab/guide.md`, generated `codelab/steps.json`; add editable SVG diagrams under `docs/diagrams/`.

**Interfaces:** Documents describe implemented contracts from Tasks 1–6, with clearly separated proposed deployment components. Diagrams show sequence, parallel-review join, conditional rework and deployment boundaries.

- [ ] Document authenticated single-tenant ingress, API/workers, isolated execution, persistent store, artifact storage, secrets, OIDC/roles, logging and backup boundaries. Explicitly mark components not implemented in local product.
- [ ] Define operational runbooks for recovery/reconciliation, cancellation, credential rotation, backup restoration, rollback, audit retention and monitoring; state observable acceptance criteria and ownership for each.
- [ ] Document every gate, score weight, tool permission and timeout with exact implementation values and examples. Threat model covers untrusted inputs, provider output, credentials, workspace escape, approval forgery and connector side effects.
- [ ] Update tutorial with actual product screenshots, understandable diagrams and evidence walkthrough. Keep setup as only the two separate shell commands. Run `python3 scripts/build-guide.py` and verify links/assets in browser.
- [ ] Commit documents and diagrams.

## Task 8: Five-slide pitch deck and final review

**Files:** Create `pitch/mobileheal-pitch.pptx`, `pitch/mobileheal-pitch.pdf` if supported by verified export, slide previews, and `pitch/README.md`; keep authoring source in `pitch/build-deck.mjs`.

**Interfaces:** Exactly five editable slides following the approved spec: product/problem; experience; agent workflow; trust/control; deployment/adoption. Slides use final implementation evidence and speaker notes for technical detail/status, not invented performance metrics.

- [ ] Read presentations visual/implementation/quick-start/finalization references and locate bundled runtime; use JavaScript artifact-tool, editable shapes/arrows and the supplied diagram reference's restrained visual style.
- [ ] Build the five-slide deck with original diagrams and actual product screenshot where useful. Keep confidence labeled evidence score, production prerequisites visible, and demo capabilities distinct from live services.
- [ ] Render and inspect all five slides for text fit, arrow routing, labels, contrast, hierarchy and audience comprehension. Fix issues, export verified deliverable and validate slide count/editability.
- [ ] Run the acceptance harness and relevant final checks; perform whole-branch review against the approved spec. Resolve material findings and repeat only affected checks. Update the verification record with honest remaining limits.
- [ ] Commit and push to the requested repository; deliver product/tutorial URLs and verified pitch artifact. Do not deploy publicly or claim unverified live/native readiness.

## Execution choice

Recommended: subagent-driven implementation with independent task reviews because a gate bypass or duplicated mutation could invalidate the product's central safety claim. Execute tasks in order; shared interfaces and workflow integration require sequential coordination. The alternative is native execution in this chat with a whole-branch review after implementation.

## Approved expansion to Task 6

Create `backend/app/static/workflow-map.html`, `.css` and `.js` as an original animated five-source diagram. Add a discoverable workflow link from the application shell and tutorial. Test source switching, pause/replay, rework, keyboard and reduced-motion/static behavior; show sample mode and connector status explicitly. Apply shared design improvements to the existing shell and page components, inspect every named existing route and preserve their functional actions. Each UI task receives independent review. The expanded plan and reviewer-based execution were explicitly approved by the user.

## As-built completion record

The approved local product, expanded workflow/UI, production design and five-slide deck are implemented and independently reviewed. See docs/IMPLEMENTATION-LEDGER.md and docs/VERIFICATION.md for exact evidence and limits. End-to-end tests live in test_harness_workflows.py plus migrated flow-control/demo tests; diagrams are editable native SVG in the workflow page, Mermaid in technical documents and native objects in the deck. The final deck path is pitch/output/MobileHeal-final.pptx; PDF export was unavailable. Rollback fails closed pending its own trusted policy and verification. Production identity/native isolation/live integrations remain deployment prerequisites. The checklist above preserves the original plan rather than implying those deployment prerequisites were implemented.
