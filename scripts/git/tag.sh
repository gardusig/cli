#!/usr/bin/env bash
# cli git wrapper
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_cli git tag "$@"
