#!/usr/bin/env bash
# Run focused unit + integration tests for cli drive.
set -euo pipefail
# shellcheck source=scripts/test/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
run_package drive "$@"
