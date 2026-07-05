#!/usr/bin/env bash
# @git-deploy — tag main when it differs from latest tag and no open PRs block release.
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_cli git deploy "$@"
