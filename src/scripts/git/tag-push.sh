#!/usr/bin/env bash
# Reconcile a git tag with origin (@git-tag-push).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"
exec_cli git tag push "$@"
