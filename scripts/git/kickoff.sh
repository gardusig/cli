#!/usr/bin/env bash
# @git-kickoff — prep main and start feature branch
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_shuttle git kickoff "$@"
