#!/usr/bin/env bash
# Install Python dependencies, then run the portal/backend and codelab together.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
PYTHON="${PYTHON:-python3}"
APP_PORT="${MOBILEHEAL_PORT:-8000}"
GUIDE_PORT="${CODELAB_PORT:-8080}"
command -v "$PYTHON" >/dev/null || { echo 'Install Python 3.10+ first (3.12 recommended).'; exit 1; }
command -v git >/dev/null || { echo 'Install Git first.'; exit 1; }
"$PYTHON" - "$APP_PORT" "$GUIDE_PORT" <<'PY'
import socket, sys
if sys.version_info < (3, 10):
    sys.exit('Python 3.10+ is required. Try PYTHON=python3.12 bash start.sh')
ports = sys.argv[1:]
if ports[0] == ports[1]:
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
if [[ ! -x backend/.venv/bin/python ]]; then
  "$PYTHON" -m venv backend/.venv
fi
VENV_PYTHON="$ROOT/backend/.venv/bin/python"
echo 'Installing required libraries in backend/.venv…'
"$VENV_PYTHON" -m pip install -r backend/pip-requirements.lock.txt
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
MOBILEHEAL_PORT="$APP_PORT" "$VENV_PYTHON" scripts/demo.py &
APP_PID=$!
"$VENV_PYTHON" -m http.server "$GUIDE_PORT" --bind 127.0.0.1 --directory "$ROOT/codelab" &
GUIDE_PID=$!
"$VENV_PYTHON" - "$APP_PORT" "$GUIDE_PORT" <<'PY'
import sys, time, urllib.request
urls = [f'http://127.0.0.1:{sys.argv[1]}/api/demo-mode', f'http://127.0.0.1:{sys.argv[2]}/']
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
printf '\nMobileHeal: %s\nCodelab:    %s\nKeep this terminal open. Ctrl+C stops both servers.\n\n' "$APP_URL" "$GUIDE_URL"
if [[ "${OPEN_BROWSER:-1}" != 0 ]]; then
  if command -v open >/dev/null; then
    open "$APP_URL" "$GUIDE_URL" || true
  elif command -v xdg-open >/dev/null; then
    xdg-open "$APP_URL" >/dev/null 2>&1 || true
    xdg-open "$GUIDE_URL" >/dev/null 2>&1 || true
  fi
fi
while kill -0 "$APP_PID" 2>/dev/null && kill -0 "$GUIDE_PID" 2>/dev/null; do
  sleep 1
done
echo 'A server stopped; shutting down the other server.'
exit 1
