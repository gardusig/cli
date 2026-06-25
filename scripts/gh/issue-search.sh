#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_cli gh issue search "$@"
