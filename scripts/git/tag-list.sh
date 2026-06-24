#!/usr/bin/env bash
# List local and remote git tags (@git-tag-list).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"
exec_cli git tag list "$@"
