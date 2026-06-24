#!/usr/bin/env bash
# Shared PyPI script paths (sources repo scripts/_common.sh).
set -euo pipefail

PYPI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${CLI_ROOT:-$(cd "$PYPI_DIR/../.." && pwd)}"
# shellcheck source=../_common.sh
source "$ROOT/scripts/_common.sh"

export CLI_DIST_DIR="${CLI_DIST_DIR:-$ROOT/dist}"
PACKAGE_NAME="gardusig-cli"

require_pypi_token() {
  load_repo_env
  if [[ -z "${PYPI_API_TOKEN:-}" ]]; then
    echo "ERROR: PYPI_API_TOKEN is not set (add to .env or export before publish)" >&2
    echo "Create a token: https://pypi.org/manage/account/token/" >&2
    return 1
  fi
}
