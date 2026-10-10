# Product acceptance

Run `bash scripts/verify-product.sh` for required focused product checks. It exits nonzero for failed tests and writes `.mobileheal/product-verification.xml`. It does not represent the inherited full suite, native device certification or live connector validation.

The release decision requires current artifact-bound evidence, trusted check/reviewer manifests and human approval. Score components must show their actual source and timestamps. Unavailable verification never counts as passed; production identity and isolated native execution are deployment requirements.

The browser acceptance journey must exercise the real application: create a requirement, approve design, inspect generated branch and reviews, execute verification, satisfy human gates and merge locally. A separate animated sample explains the same control flow without pretending it executed agent work. Choose each of the five sources and test pass/rework, pause/replay/static and keyboard/mobile behavior.

Negative tests cover absent/failed/stale receipts, critical or absent reviewers, invalid schema, unknown mutation outcomes, duplicate operation identities, cancelled/late output, budget exhaustion, forbidden paths, credentials and unavailable isolation. Production claims remain blocked until the target environment demonstrates identity, isolation, backup restoration, capacity, native builds and live integrations.

See VERIFICATION.md for actual executed results and remaining failures; this checklist is not evidence of completion by itself.
