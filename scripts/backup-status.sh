#!/usr/bin/env bash
# Show git-tags backup status (iCloud) vs git tags (@backup-status).
set -euo pipefail

ROOT="${CLI_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

# shellcheck source=git/_common.sh
source "$ROOT/scripts/git/_common.sh"
exec_cli drive status "$@"
