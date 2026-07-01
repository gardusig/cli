#!/usr/bin/env bash
set -euo pipefail
export REPO_DOCKER_SOCKET=1
# shellcheck source=../docker/_common.sh
source "$(dirname "$0")/../docker/_common.sh"
docker_run_target_with_repo version "${REPO_VERSION_TIMEOUT_SEC:-120}"
