#!/usr/bin/env bash
# Shared helpers for all src/scripts/* wrappers (shell only — logic lives in src/).
set -euo pipefail

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$(basename "$(dirname "$SCRIPT_ROOT")")" == "src" ]]; then
  DEFAULT_ROOT="$(cd "$SCRIPT_ROOT/../.." && pwd)"
else
  DEFAULT_ROOT="$(cd "$SCRIPT_ROOT/.." && pwd)"
fi
ROOT="${CLI_ROOT:-$DEFAULT_ROOT}"

load_repo_env() {
  if [[ -f "$ROOT/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$ROOT/.env"
    set +a
  fi
}

resolve_cli() {
  if [[ -n "${CLI_BIN:-}" ]]; then
    printf '%s\n' "$CLI_BIN"
    return 0
  fi
  if command -v cli >/dev/null 2>&1; then
    printf '%s\n' "cli"
    return 0
  fi
  if [[ -x "$ROOT/.venv/bin/python" ]]; then
    printf '%s\n' "$ROOT/.venv/bin/python -m src"
    return 0
  fi
  echo "ERROR: cli not found. Run pip install -e . or pip install gardusig-cli" >&2
  return 1
}

exec_cli() {
  local cli_cmd
  cli_cmd=$(resolve_cli)
  # shellcheck disable=SC2086
  exec $cli_cmd "$@"
}
