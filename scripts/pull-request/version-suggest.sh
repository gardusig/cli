#!/usr/bin/env bash
# Print the next PyPI-compatible package version (does not write files).
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

exec bash "$(dirname "${BASH_SOURCE[0]}")/set-version.sh" --dry-run
