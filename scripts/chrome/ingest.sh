#!/usr/bin/env bash
# Chrome → local: ingest bookmarks into configured path.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${SHUTTLE_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

# shellcheck source=../git/_common.sh
source "$ROOT/scripts/git/_common.sh"
exec_shuttle chrome bookmarks ingest "$@"
