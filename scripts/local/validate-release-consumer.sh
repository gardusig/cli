#!/usr/bin/env bash
# Deprecated wrapper — use scripts/local/preview-release-workflow.sh
set -euo pipefail
exec "$(dirname "${BASH_SOURCE[0]}")/preview-release-workflow.sh" "$@"
