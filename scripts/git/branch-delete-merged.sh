#!/usr/bin/env bash
# @git-branch-delete-merged — cursor-skills/skills/git/branch/delete/merged
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_cli git branch delete --merged "$@"
