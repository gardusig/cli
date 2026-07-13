#!/usr/bin/env bash
set -euo pipefail
dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/pull-request/consumer/_common.sh
source "$dir/consumer/_common.sh"
# shellcheck source=scripts/_common.sh
source "$dir/../_common.sh"
# shellcheck source=scripts/pull-request/_smoke.sh
source "$dir/_smoke.sh"

export PYPI_INDEX="${PYPI_INDEX:-testpypi}"
consumer_install_package
exec bash "$dir/consumer/run.sh" "$@"
