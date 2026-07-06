#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck disable=SC1091
source "$SCRIPTS_ROOT/_common.sh"

require_workspace() {
  if [[ -z "${WORKSPACE:-}" ]]; then
    echo "ERROR: WORKSPACE is required" >&2
    exit 1
  fi
  if [[ ! -d "$WORKSPACE" ]]; then
    echo "ERROR: WORKSPACE is not a directory: $WORKSPACE" >&2
    exit 1
  fi
}

run_python_module() {
  local python_bin="${PYTHON_BIN:-python3}"
  "$python_bin" -m "$@"
}

