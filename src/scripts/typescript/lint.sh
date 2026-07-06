#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

require_workspace
cd "$WORKSPACE"

if [[ ! -d node_modules ]]; then
  if [[ -f package-lock.json ]]; then
    npm ci
  else
    npm install
  fi
fi

for script_name in format:check lint typecheck; do
  if npm run | grep -qE "^[[:space:]]+$script_name$"; then
    npm run "$script_name"
  fi
done

echo "typescript lint ok"

