#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

require_workspace
cd "$WORKSPACE"

mapfile -t files < <(find scripts -type f -name '*.sh' 2>/dev/null | sort || true)
if [[ ${#files[@]} -eq 0 ]]; then
  echo "shell lint skipped: no src/scripts/*.sh"
  exit 0
fi

for file in "${files[@]}"; do
  bash -n "$file"
done

echo "shell lint ok"

