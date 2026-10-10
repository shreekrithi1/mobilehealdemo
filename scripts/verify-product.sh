#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
PYTHON="$ROOT/backend/.venv/bin/python"
[[ -x "$PYTHON" ]] || { echo 'Run bash run-application.sh first.'; exit 1; }
exec "$PYTHON" -m pytest -q tests/test_harness_policy.py tests/test_harness_store.py tests/test_harness_execution.py tests/test_harness_tools.py tests/test_harness_redaction.py tests/test_harness_workflows.py tests/test_harness_api.py tests/test_rules_contract.py tests/test_security.py tests/test_watchdog.py tests/test_flow_control.py tests/test_demo_mode.py --junitxml="$ROOT/.mobileheal/product-verification.xml"
