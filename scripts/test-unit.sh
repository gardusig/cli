#!/usr/bin/env bash
# Unit tests in cli:unit (Docker on macOS or Linux; same image as CI).
set -euo pipefail
export CLI_DOCKER_TARGET=unit
export CLI_DOCKER_IMAGE="${CLI_DOCKER_IMAGE:-cli:unit}"
# shellcheck source=docker/common.sh
source "$(dirname "$0")/docker/common.sh"

INNER="$(docker_copy_workspace_script)
cd '$CONTAINER_WORK'
$(docker_init_git_workspace "$CONTAINER_WORK" "docker unit snapshot")
./scripts/docker/run-unit.sh"

docker_run_in_workspace "$INNER"
