#!/usr/bin/env bash
# @git-revert — cursor-skills/skills/git/revert
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_cli git revert "$@"
