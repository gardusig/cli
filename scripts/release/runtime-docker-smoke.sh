#!/usr/bin/env bash
# Read-only integration smoke against a pulled runtime image via docker run.
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

_run_runtime_docker_smoke() {
  local version="${CLI_VERSION:?CLI_VERSION required}"
  local fixtures_dir="/workspace/tests/fixtures/config"
  if [[ ! -d "$fixtures_dir" ]]; then
    echo "fixtures dir missing: ${fixtures_dir}" >&2
    exit 1
  fi
  docker run --rm \
    -v "${fixtures_dir}:/config:ro" \
    -e CLI_PROFILE=test \
    -e CLI_CONFIG_DIR=/config \
    --entrypoint bash \
    "${RUNTIME_IMAGE:?RUNTIME_IMAGE required}:${version}" \
    -ec '
      set -euo pipefail
      got="$(cli --version)"
      if [[ "$got" != "'"${version}"'" ]]; then
        echo "runtime version mismatch: expected '"${version}"', got ${got}" >&2
        exit 1
      fi
      cli --help >/dev/null
      cli languages list >/dev/null
      cli gh policy list | grep -Fq pr-merge
    '
}

stage_run_with_timeout "${CI_RELEASE_SMOKE_TIMEOUT}" _run_runtime_docker_smoke
echo "runtime docker integration passed: ${RUNTIME_IMAGE:?RUNTIME_IMAGE required}:${CLI_VERSION:?CLI_VERSION required}"
