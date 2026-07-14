#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

version="${CLI_VERSION:?CLI_VERSION required}"

_push_runtime_image() {
  docker push "${RUNTIME_IMAGE}:${CLI_VERSION}"
  docker push "${RUNTIME_IMAGE}:latest"
}

stage_run_with_timeout "${CI_DOCKER_PUSH_TIMEOUT}" _push_runtime_image
