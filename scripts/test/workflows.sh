#!/usr/bin/env bash
# Host pytest for workflow E2E modules (gh mocked; git uses temp dirs in tests).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
# shellcheck source=../_common.sh
source "$ROOT/scripts/_common.sh"
load_repo_env

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="python3"
else
  echo "ERROR: no python; run ./scripts/pypi/install.sh" >&2
  exit 1
fi

export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONUNBUFFERED=1
export CLI_CONFIG_DIR="${CLI_CONFIG_DIR:-$ROOT/config/ci}"

echo "==> workflow E2E tests"
exec "$PY" -m pytest tests/workflows/ -v --tb=short "$@"
