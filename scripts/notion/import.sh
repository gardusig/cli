#!/usr/bin/env bash
# Local tasks → Notion (@notion-import).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${SHUTTLE_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

# shellcheck source=../git/_common.sh
source "$ROOT/scripts/git/_common.sh"
exec_shuttle notion deploy "$@"
