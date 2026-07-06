#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

require_workspace
cd "$WORKSPACE"

if npm run | grep -qE '^[[:space:]]+test:coverage$'; then
  npm run test:coverage
elif npm run | grep -qE '^[[:space:]]+test$'; then
  npm test
else
  echo "typescript test skipped: no test script"
fi

