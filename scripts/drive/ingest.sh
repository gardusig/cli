#!/usr/bin/env bash
# Zip all git tags into local git-tags/ for configured repos or one PATH (@drive-ingest).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${SHUTTLE_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

# shellcheck source=../git/_common.sh
source "$ROOT/scripts/git/_common.sh"
exec_shuttle drive ingest "$@"
