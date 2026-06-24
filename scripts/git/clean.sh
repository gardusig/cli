#!/usr/bin/env bash
# @git-clean — remove build/test artifacts (git clean -fdx); pass --yes
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_cli git clean "$@"
