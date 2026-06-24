#!/usr/bin/env bash
# Deploy local task pairs to Notion (uses config/release + env secrets).
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/../_common.sh"

require_notion_token
export NOTION_TOKEN
export CLI_CONFIG_DIR="${CLI_CONFIG_DIR:-$ROOT/config/release}"
exec_cli notion deploy --yes "$@"
