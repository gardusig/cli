#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

version="${CLI_RELEASE_VERSION:?CLI_RELEASE_VERSION required}"
if [[ -z "${PYPI_API_TOKEN:-}" ]]; then
  echo "PYPI_API_TOKEN is not set" >&2
  exit 1
fi

bash "$(dirname "${BASH_SOURCE[0]}")/build.sh" pypi \
  --build-arg "CLI_RELEASE_VERSION=${version}" \
  --build-arg "PYPI_API_TOKEN=${PYPI_API_TOKEN}"
