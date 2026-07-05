#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

require_workspace
cd "$WORKSPACE"

if npm run | grep -qE '^[[:space:]]+build$'; then
  npm run build
else
  echo "typescript build skipped: no build script"
fi

