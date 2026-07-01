#!/usr/bin/env bash
# Regression gate — workflow + pack checks (third test phase after integration).
set -euo pipefail
export REPO_DOCKER_SOCKET=1
# shellcheck source=../docker/_common.sh
source "$(dirname "$0")/../docker/_common.sh"
run_regression_tests
