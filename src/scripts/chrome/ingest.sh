#!/usr/bin/env bash
# Chrome → local: ingest bookmarks into configured path.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${CLI_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"

# shellcheck source=../git/_common.sh
source "$(cd "$SCRIPT_DIR/../git" && pwd)/_common.sh"
exec_cli chrome bookmarks ingest "$@"
