#!/usr/bin/env bash
# Onboard: interactive shell in a container with a bootstrapped copy of the repo.
set -euo pipefail
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
export CLI_DOCKER_TARGET="${CLI_DOCKER_TARGET:-integration}"
export CLI_DOCKER_IMAGE="${CLI_DOCKER_IMAGE:-cli:integration}"

docker_ensure_image
docker run --rm -it \
  -v "$ROOT:$CONTAINER_SRC:ro" \
  -e CLI_DOCKER_INTEGRATION=1 \
  "$IMAGE" \
  bash -c "
    set -euo pipefail
    $(docker_copy_workspace_script)
    cd '$CONTAINER_WORK'
    CLI_BOOTSTRAP_DEV=1 ./scripts/docker/bootstrap.sh
    echo ''
    echo 'Bootstrapped workspace: $CONTAINER_WORK'
    echo 'Try: python -m gardusig_cli --help'
    echo ''
    exec bash
  "
