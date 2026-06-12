#!/usr/bin/env bash
# Local → Chrome: deploy bookmarks backup into Chrome.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${SHUTTLE_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

# shellcheck source=../git/_common.sh
source "$ROOT/scripts/git/_common.sh"
exec_shuttle chrome bookmarks deploy "$@"
