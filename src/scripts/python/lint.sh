#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

require_workspace
cd "$WORKSPACE"

mapfile -t files < <(find . \
  \( -path './.git' -o -path './.venv' -o -path './node_modules' \) -prune -o \
  -type f -name '*.py' -print | sort)

if [[ ${#files[@]} -eq 0 ]]; then
  echo "python lint skipped: no Python files"
  exit 0
fi

python3 -m py_compile "${files[@]}"
echo "python lint ok"

