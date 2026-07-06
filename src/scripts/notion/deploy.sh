#!/usr/bin/env bash
# Local → Notion: deploy configured task root to board
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${CLI_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"

# shellcheck source=../git/_common.sh
source "$(cd "$SCRIPT_DIR/../git" && pwd)/_common.sh"
exec_cli notion deploy "$@"
