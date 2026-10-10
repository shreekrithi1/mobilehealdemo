#!/usr/bin/env bash
# Install Python dependencies, then run the portal/backend and codelab together.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
MODE="${1:-all}"
case "$MODE" in all|application|tutorial) ;; *) echo 'Unknown launcher mode'; exit 1;; esac
PYTHON="${PYTHON:-python3}"
if [[ "$PYTHON" == python3 ]]; then
  for candidate in python3.12 python3.13 python3.11 python3.10 python3; do
    if command -v "$candidate" >/dev/null; then PYTHON="$candidate"; break; fi
  done
fi
APP_PORT="${MOBILEHEAL_PORT:-8000}"
GUIDE_PORT="${CODELAB_PORT:-8080}"
command -v "$PYTHON" >/dev/null || { echo 'Install Python 3.10+ first (3.12 recommended).'; exit 1; }
[[ "$MODE" == tutorial ]] || command -v git >/dev/null || { echo 'Install Git first.'; exit 1; }
"$PYTHON" - "$APP_PORT" "$GUIDE_PORT" "$MODE" <<'PY'
import socket, sys
if sys.version_info < (3, 10):
    sys.exit('Python 3.10+ is required. Try PYTHON=python3.12 bash start.sh')
ports = sys.argv[1:3] if sys.argv[3] == 'all' else [sys.argv[1] if sys.argv[3] == 'application' else sys.argv[2]]
if len(ports) == 2 and ports[0] == ports[1]:
    sys.exit('Application and guide ports must differ.')
for value in ports:
    try:
        port = int(value)
        if not 1 <= port <= 65535:
            raise ValueError()
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', port))
    except (ValueError, OSError) as exc:
        sys.exit(f'Cannot use port {value}: {exc}. Choose MOBILEHEAL_PORT and CODELAB_PORT.')
PY
if [[ "$MODE" != tutorial ]]; then
if [[ ! -x backend/.venv/bin/python ]]; then
  "$PYTHON" -m venv backend/.venv
fi
VENV_PYTHON="$ROOT/backend/.venv/bin/python"
echo 'Installing required libraries in backend/.venv…'
"$VENV_PYTHON" -m pip install -r backend/pip-requirements.lock.txt
else
  VENV_PYTHON="$PYTHON"
fi
APP_PID=''
GUIDE_PID=''
cleanup() {
  trap - EXIT INT TERM
  [[ -z "$APP_PID" ]] || kill "$APP_PID" 2>/dev/null || true
  [[ -z "$GUIDE_PID" ]] || kill "$GUIDE_PID" 2>/dev/null || true
  [[ -z "$APP_PID" ]] || wait "$APP_PID" 2>/dev/null || true
  [[ -z "$GUIDE_PID" ]] || wait "$GUIDE_PID" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
if [[ "$MODE" != tutorial ]]; then
MOBILEHEAL_PORT="$APP_PORT" "$VENV_PYTHON" scripts/demo.py &
APP_PID=$!
fi
if [[ "$MODE" != application ]]; then
"$VENV_PYTHON" -m http.server "$GUIDE_PORT" --bind 127.0.0.1 --directory "$ROOT/codelab" &
GUIDE_PID=$!
fi
"$VENV_PYTHON" - "$APP_PORT" "$GUIDE_PORT" "$MODE" <<'PY'
import sys, time, urllib.request
urls = [f'http://127.0.0.1:{sys.argv[1]}/api/demo-mode', f'http://127.0.0.1:{sys.argv[2]}/']
if sys.argv[3] == 'application': urls = urls[:1]
if sys.argv[3] == 'tutorial': urls = urls[1:]
for url in urls:
    deadline = time.monotonic() + 60
    while True:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    break
        except Exception:
            if time.monotonic() >= deadline:
                sys.exit(f'Startup failed: {url}. Check the server output above.')
            time.sleep(0.5)
PY
APP_URL="http://localhost:$APP_PORT/#new"
GUIDE_URL="http://localhost:$GUIDE_PORT/?appPort=$APP_PORT#0"
URLS=()
[[ "$MODE" == tutorial ]] || URLS+=("$APP_URL")
[[ "$MODE" == application ]] || URLS+=("$GUIDE_URL")
printf '\nReady: %s\n' "${URLS[@]}"
echo 'Keep this terminal open. Ctrl+C stops the server.'
if [[ "${OPEN_BROWSER:-1}" != 0 ]]; then
  if command -v open >/dev/null; then
    open "${URLS[@]}" || true
  elif command -v xdg-open >/dev/null; then
    for url in "${URLS[@]}"; do xdg-open "$url" >/dev/null 2>&1 || true; done
  fi
fi
while { [[ -z "$APP_PID" ]] || kill -0 "$APP_PID" 2>/dev/null; } && { [[ -z "$GUIDE_PID" ]] || kill -0 "$GUIDE_PID" 2>/dev/null; }; do
  sleep 1
done
echo 'A server stopped; shutting down the other server.'
exit 1
