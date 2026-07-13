#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

version="${CLI_RELEASE_VERSION:?CLI_RELEASE_VERSION required}"

bash "$(dirname "${BASH_SOURCE[0]}")/build.sh" testpypi-consumer \
  --build-arg "CLI_RELEASE_VERSION=${version}"
