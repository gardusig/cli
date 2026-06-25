#!/usr/bin/env bash
# @git-branch-current
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_cli git branch current "$@"
