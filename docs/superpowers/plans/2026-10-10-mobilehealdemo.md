# MobileHeal codelab implementation plan

Goal: ship the supplied application with a locally served illustrated codelab.
Spec: ../specs/2026-10-10-mobilehealdemo-design.md

1. Package tracked source without runtime data, credentials, generated change records or existing history.
2. Add a headless isolated demo launcher and a static guide server, both bound to loopback.
3. Capture requirements, design, review/testing, crash and data-health screenshots on the isolated instance.
4. Author numbered lessons with commands, expected results, troubleshooting and optional native-client instructions.
5. Build an accessible responsive guide with sidebar navigation, hash links, copy controls and local progress.
6. Verify the backend suite, exercise the documented workflow, inspect the guide and check assets.
7. Commit and push the finished repository to the user-authorized GitHub destination.

Use the supplied source as the application reference. Treat Android and iOS build instructions as unverified unless the SDK checks succeed. Do not claim simulated PRs are real GitHub PRs.
