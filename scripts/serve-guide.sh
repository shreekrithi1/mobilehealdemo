#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 -m http.server "${CODELAB_PORT:-8080}" --bind 127.0.0.1 --directory "$ROOT/codelab"
