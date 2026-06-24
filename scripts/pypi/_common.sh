#!/usr/bin/env bash
# Shared PyPI script paths (sources repo scripts/_common.sh).
set -euo pipefail

PYPI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${CLI_ROOT:-$(cd "$PYPI_DIR/.." && pwd)}"
# shellcheck source=../_common.sh
source "$ROOT/scripts/_common.sh"

export CLI_DIST_DIR="${CLI_DIST_DIR:-$ROOT/dist}"
