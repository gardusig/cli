#!/usr/bin/env bash
# Install gardusig-cli from PyPI with index propagation backoff (release runtime stage).
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

_runtime_install() {
  local version="${CLI_VERSION:?CLI_VERSION required}"
  export PYPI_INDEX=pypi
  pypi_wait_and_install_package "gardusig-cli" "$version" pypi
}

stage_run_with_timeout "${CI_RUNTIME_INSTALL_TIMEOUT}" _runtime_install
