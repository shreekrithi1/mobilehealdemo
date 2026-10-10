# Guardrails and evidence gates

## Evidence confidence

The policy calculates an evidence score, not a probability that the change is correct. Acceptance coverage contributes 30 points, executed verification 30, required review completeness 25 and provenance 15. Every component exposes numerator, denominator, source and timestamp. Missing, skipped, stale and unavailable checks earn zero. The initial threshold is 85; it cannot override a mandatory blocker.

Trusted stage configuration specifies required evidence identifiers and reviewer roles. Removing a failed required receipt cannot satisfy that manifest. Executed command receipts require a zero exit code, duration and valid argument vector; a label saying “passed” cannot turn a nonzero exit into passing evidence. Approval binds to the exact artifact revision and commit.

Critical findings, failed/absent mandatory evidence, missing reviewers, stale artifacts, unauthorized actions, unresolved mutation outcomes and missing human approval block advancement. Changed artifacts need fresh review. A score alone never authorizes release.

## Tool boundary

Only host-defined named tools and closed argument schemas are accepted. The model cannot supply a shell string, change the registry or declare its own authority. Workspace paths are resolved and checked against source allowlists; traversal, symlinks, credentials, Git internals and policy files are denied.

Tools require OS isolation by default. Without a supported isolation runtime they return unavailable before launch. The local fixed Git status/diff adapters and application-owned deterministic rules/greeting verification scripts are explicit host exceptions: they use argument vectors, stripped credential environment, bounded output and process-group cleanup. Python exceptions are limited to host-defined assertions over validated rules or exact canonical demo templates; they do not authorize arbitrary repository tests, generated Python or mutable package imports. Process groups are not an OS sandbox and cannot guarantee termination of detached descendants. Native or arbitrary generated execution remains unavailable where isolation is required; a deployment adapter must provide that boundary.

Default execution deadline is 300 seconds; maximum host-configured bound is 3600 seconds. Captured output is capped at 64 KiB by default. Cancellation and timeouts fail the receipt. Missing executables are unavailable rather than passed. Secret redaction runs before the provider/log boundary, including structured and quoted credentials and incomplete private-key output.

## Durable state

A run represents one stage and one input commit; workflow-level grouping links stage runs. SQLite revision checks reject stale transitions. Trusted stage identity and attempt number are stored before producer execution, so a failed attempt cannot expose an older snapshot for approval. The initial attempt plus two rework attempts is the maximum.

Mutations use a host-approved named operation and a canonical identity derived from workspace, artifact commit and operation. An unknown mutation outcome blocks subsequent execution. It must be reconciled with a receipt, never retried using a newly invented key.

Reviewers receive frozen independent input copies. The join waits for every required role within 120 seconds. Missing, invalid or late results do not advance state. In-process timed-out reviewer threads can continue; their outputs are discarded. Production worker isolation and lifecycle supervision remain deployment requirements.

Reconciliation is an operator/startup action performed with workers stopped. Do not call it concurrently with live execution. Audit events are persistent application records; they are not claimed tamper-proof.

## Human identity

Local demo identities are visibly simulated. Production approvals require authenticated identities, role checks and separation of author and releaser. An actor field supplied in request JSON is not authentication. Production identity integration is a release prerequisite, not something a local demo badge proves.

## Reviewer scope

Each stage has two distinct deterministic evidence reviewers. Requirements use acceptance/ambiguity, design uses UX/acceptance, code uses correctness/security, tests use coverage/receipt integrity, incidents use causal/replay, data uses quality/privacy, and release uses policy/operability. They inspect manifests, provenance, acceptance assertions, redacted summaries and executed receipts as appropriate. Their role names do not establish semantic correctness, device safety or a security audit. Those require separate human and runtime verification. Requirements and design record deterministic non-execution inspection; code, test, incident and release evidence includes actual supported command receipts.
