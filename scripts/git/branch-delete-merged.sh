#!/usr/bin/env bash
# @git-branch-delete-merged — cursor-skills/skills/git/branch/delete/merged
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck source=scripts/lib/exec_cli.sh
source "$ROOT/scripts/lib/exec_cli.sh"
exec_cli git branch delete --merged "$@"
