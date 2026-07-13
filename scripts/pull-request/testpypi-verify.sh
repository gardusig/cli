#!/usr/bin/env bash
# Post-TestPyPI path: install from index → consumer smoke → integration suite.
set -euo pipefail
dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/_common.sh
source "$dir/../_common.sh"
# shellcheck source=scripts/pull-request/consumer/_common.sh
source "$dir/consumer/_common.sh"

export PYPI_INDEX="${PYPI_INDEX:-testpypi}"
consumer_install_package

bash "$dir/consumer/run.sh"
bash "$dir/testpypi-integration.sh"
