#!/usr/bin/env bash
# Shared helpers for scripts/git wrappers (maps to cursor-skills git skills).
set -euo pipefail

GIT_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${CLI_ROOT:-$(cd "$GIT_SCRIPT_DIR/../.." && pwd)}"

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
    printf '%s\n' "$ROOT/.venv/bin/python -m cli"
    return 0
  fi
  echo "ERROR: cli not found. Run ./scripts/bootstrap.sh or ./scripts/install.sh" >&2
  return 1
}

exec_cli() {
  local cli_cmd
  cli_cmd=$(resolve_cli)
  # shellcheck disable=SC2086
  exec $cli_cmd "$@"
}
