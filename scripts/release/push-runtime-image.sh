#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

version="${CLI_VERSION:?CLI_VERSION required}"

docker push "${RUNTIME_IMAGE}:${version}"
docker push "${RUNTIME_IMAGE}:latest"
