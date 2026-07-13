#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

version="${CLI_VERSION:?CLI_VERSION required}"

bash "$(dirname "${BASH_SOURCE[0]}")/build.sh" runtime \
  --build-arg "CLI_VERSION=${version}" \
  -t "${RUNTIME_IMAGE}:${version}" \
  -t "${RUNTIME_IMAGE}:latest"
