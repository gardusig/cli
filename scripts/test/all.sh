#!/usr/bin/env bash
# Print the full-suite contract (nightly / ci:full safety net).
set -euo pipefail
# shellcheck source=scripts/test/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
root="$(repo_root)"
export CLI_CONFIG_DIR="${CLI_CONFIG_DIR:-config/ci}"
cd "$root"
exec python3 -m src test packages suite --format "${FORMAT:-table}" "$@"
