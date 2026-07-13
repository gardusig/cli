#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

version="${CLI_VERSION:?CLI_VERSION required}"

docker pull "${RUNTIME_IMAGE}:${version}"
docker run --rm "${RUNTIME_IMAGE}:${version}" --version
