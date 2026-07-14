#!/usr/bin/env bash
# Shared helpers for post-install consumer integration (pip-installed cli binary only).
set -euo pipefail

consumer_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")" && pwd
}

consumer_install_package() {
  # shellcheck source=scripts/_common.sh
  source "$(dirname "${BASH_SOURCE[0]}")/../../_common.sh"
  local version="${CLI_RELEASE_VERSION:?CLI_RELEASE_VERSION is required}"
  local index="${PYPI_INDEX:-testpypi}"
  pypi_wait_and_install_package "gardusig-cli" "$version" "$index"
}
