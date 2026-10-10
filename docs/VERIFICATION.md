# Verification record

Validated on 10 October 2026 on macOS with Python 3.12 and a fresh temporary virtual environment. The package preserves the supplied application's behavior; this work adds the illustrated codelab and launch helpers.

## Observed working

- Installed the declared backend dependencies into a fresh environment; `backend/pip-requirements.lock.txt` records the resolved versions.
- Started the copied application through `scripts/demo.py` on loopback port 8010. The original server on 8000 was left running.
- Created an isolated Git workspace, a separate demo database and a no-key parser-mode instance.
- Exercised the documented banner requirement in the browser: interpretation, design approval, generated code, local PR, tests and merge.
- Both generated test cases passed and were saved. Two approvals were simulated using explicitly fictional `Demo QA` and `Demo Product Owner` roles. Local merge commit: `c1b01990ef` in the isolated workspace. This is not a public GitHub PR or production deployment.
- Triggered the missing-name crash: the backend returned HTTP 500, an incident was recorded, the mock Jira defect was created, diagnosis was displayed, and approval generated a fix PR with a successful replay of the captured input. The crash-fix PR was not merged during documentation capture.
- Loaded synthetic sample data and scanned data health: 7 open issues, including missing required fields, invalid values and duplicate emails.
- Captured seven original tutorial screenshots on the isolated instance; all referenced assets resolve.
- Served the guide on loopback port 8080. Verified lesson links, filtering, progress toggle, screenshot dialog and code-copy feedback. The IAB clipboard readback did not expose the copied text; exact OS clipboard content was not independently verified.
- Inspected desktop layout and the 390px mobile breakpoint: no horizontal document overflow, screenshot loaded, and mobile navigation opened and selected a lesson.
- Compiled both new Python helpers and checked the guide shell launcher syntax.
- Verified the launcher isolation test: source remains unchanged, runtime files and credentials are excluded, and the Android demo application flag is present in the copied workspace.
- After review, verified `?appPort=8010` rewrites the requirement lesson link to `http://localhost:8010/#new`, so the exercise stays on the selected instance.

## Inherited suite results

The complete `python -m pytest -q` run was interrupted after approximately ten minutes, with **58 passed and 22 failed** at interruption. It did not finish and must not be described as passing. Failures observed include native-build expectations, merge/review approval policy expectations, Firebase authentication tests, and Autopilot workflows remaining at PR-open state. These are observations, not a completed root-cause investigation.

The focused contract/security/data-health suites (`test_rules_contract.py`, `test_security.py`, `test_watchdog.py`) passed: **14 passed, 1 deprecation warning in 2.59 seconds**.

## Limits

- Android and iOS native builds, device execution, app-store delivery and cloud deployment were not verified.
- The supplied Android source applies Firebase plugins. The original `google-services.json` was excluded; add your own matching configuration to build that client.
- The baseline save button produces a contrast warning (3.91:1). The guide exposes this and does not claim accessibility compliance.
- External integrations and model providers were not connected with real credentials. Demo PR links, Jira defects and Figma behavior are simulated.
- Demo sample data starts additional background workflow items; issue counts can change as the lab runs.
- The copied original technical reference can describe older behavior. The codelab follows the controls observed in this supplied version.
