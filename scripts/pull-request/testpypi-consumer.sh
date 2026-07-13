#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/pull-request/consumer/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/consumer/_common.sh"

export PYPI_INDEX="${PYPI_INDEX:-testpypi}"
consumer_install_package
export CLI_CONFIG_DIR="${CLI_CONFIG_DIR:-$(dirname "${BASH_SOURCE[0]}")/consumer/fixtures/config}"
bash "$(dirname "${BASH_SOURCE[0]}")/consumer/run.sh" "$@"
