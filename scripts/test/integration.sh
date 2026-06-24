#!/usr/bin/env bash
# Integration gate: full pytest + smoke + live docker in cli:integration.
set -euo pipefail
export CLI_DOCKER_TARGET=integration
export CLI_DOCKER_IMAGE="${CLI_DOCKER_IMAGE:-cli:integration}"
# shellcheck source=../docker/common.sh
source "$(dirname "$0")/../docker/common.sh"

INNER="$(docker_copy_workspace_script)
cd '$CONTAINER_WORK'
$(docker_init_git_workspace "$CONTAINER_WORK" "docker integration snapshot")
./scripts/docker/run-integration.sh"

docker_run_in_workspace "$INNER" 1
