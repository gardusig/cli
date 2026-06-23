#!/usr/bin/env bash
# @git-branch-delete-all — cursor-skills/skills/git/branch/delete/all
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_cli git branch-delete-all "$@"
