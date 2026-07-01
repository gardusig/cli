#!/usr/bin/env bash
set -euo pipefail
export REPO_DOCKER_SOCKET=1
# shellcheck source=../docker/_common.sh
source "$(dirname "$0")/../docker/_common.sh"
echo "==> integration phase: version drift check"
"$(dirname "$0")/drift.sh"
run_integration_tests
