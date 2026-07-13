#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

base_version="${BASE_VERSION:-}"
bash "$(dirname "${BASH_SOURCE[0]}")/build.sh" version-check \
  --build-arg "BASE_VERSION=${base_version}"
