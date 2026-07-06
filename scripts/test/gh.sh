#!/usr/bin/env bash
# Run focused unit + integration tests for cli gh.
# Usage: scripts/test/gh.sh [--dry-run] [--no-unit] [extra pytest args via cli]
set -euo pipefail
# shellcheck source=scripts/test/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
run_package gh "$@"
