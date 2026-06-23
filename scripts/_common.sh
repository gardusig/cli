#!/usr/bin/env bash
# Shared helpers for all scripts/* wrappers (shell only — logic lives in cli/).
set -euo pipefail

ROOT="${CLI_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

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

require_pypi_token() {
  load_repo_env
  if [[ -z "${PYPI_API_TOKEN:-}" ]]; then
    echo "ERROR: PYPI_API_TOKEN is not set (add to .env or export before publish)" >&2
    echo "Create a token: https://pypi.org/manage/account/token/" >&2
    return 1
  fi
}

require_notion_token() {
  load_repo_env
  if [[ -z "${NOTION_TOKEN:-}" ]]; then
    echo "ERROR: NOTION_TOKEN is not set (add to .env or export before deploy)" >&2
    return 1
  fi
  if [[ -z "${NOTION_DATABASE_ID:-}" ]]; then
    echo "ERROR: NOTION_DATABASE_ID is not set (required for release deploy)" >&2
    return 1
  fi
  if [[ -z "${NOTION_TASK_ROOT:-}" ]]; then
    echo "ERROR: NOTION_TASK_ROOT is not set (path to header/body task root)" >&2
    return 1
  fi
}
