#!/usr/bin/env bash
# Notion script wrappers — shared paths and release env checks.
set -euo pipefail

NOTION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${CLI_ROOT:-$(cd "$NOTION_DIR/../../.." && pwd)}"
# shellcheck source=../_common.sh
source "$(cd "$NOTION_DIR/.." && pwd)/_common.sh"

require_notion_token() {
  load_repo_env
  if [[ -z "${NOTION_TOKEN:-}" ]]; then
    echo "ERROR: NOTION_TOKEN is not set (add to .env or export before deploy)" >&2
    return 1
  fi
  if [[ -z "${NOTION_DATABASE_ID:-}" ]]; then
    echo "ERROR: NOTION_DATABASE_ID is not set (required for release deploy)" >&2
    return 1
  fi
  if [[ -z "${NOTION_TASK_ROOT:-}" ]]; then
    echo "ERROR: NOTION_TASK_ROOT is not set (path to header/body task root)" >&2
    return 1
  fi
}
