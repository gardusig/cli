#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/_common.sh
source "${script_dir}/../_common.sh"

_pull_runtime_image() {
  docker_wait_and_pull "${RUNTIME_IMAGE:?RUNTIME_IMAGE required}" "${CLI_VERSION:?CLI_VERSION required}"
}

stage_run_with_timeout "${CI_RELEASE_SMOKE_TIMEOUT}" _pull_runtime_image
bash "${script_dir}/verify-runtime-version.sh"
bash "${script_dir}/runtime-docker-smoke.sh"
