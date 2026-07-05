#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

require_workspace
cd "$WORKSPACE"

mapfile -t files < <(find . -type f \( -name '*.cpp' -o -name '*.cc' -o -name '*.cxx' -o -name '*.hpp' -o -name '*.h' \) | sort)
if [[ ${#files[@]} -eq 0 ]]; then
  echo "cpp lint skipped: no C++ files"
  exit 0
fi

clang-format --dry-run --Werror "${files[@]}"
echo "cpp lint ok"

