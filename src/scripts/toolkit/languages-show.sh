#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

require_workspace

if [[ -z "${CLI_LANGUAGE:-}" ]]; then
  echo "ERROR: CLI_LANGUAGE is required" >&2
  exit 1
fi

run_python_module src.services.toolkit.script_api languages-show "$CLI_LANGUAGE"

