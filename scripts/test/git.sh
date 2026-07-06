#!/usr/bin/env bash
# Run focused unit + integration tests for cli git.
set -euo pipefail
# shellcheck source=scripts/test/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
run_package git "$@"
