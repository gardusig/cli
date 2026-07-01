#!/usr/bin/env bash
set -euo pipefail
export REPO_DOCKER_SOCKET=1
# shellcheck source=../docker/_common.sh
source "$(dirname "$0")/../docker/_common.sh"
docker_require
image="$(docker_image_for pypi-test)"
docker_build_target pypi-test
timeout "${REPO_PYPI_TEST_TIMEOUT_SEC:-480}" docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e TESTPYPI_API_TOKEN="${TESTPYPI_API_TOKEN:-}" \
  -e CLI_PYPI_TEST_VERSION="${CLI_PYPI_TEST_VERSION:-1.0.0}" \
  "$image"
