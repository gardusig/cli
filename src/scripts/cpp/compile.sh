#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

require_workspace
cd "$WORKSPACE"

if [[ -f CMakeLists.txt ]] && command -v cmake >/dev/null 2>&1; then
  cmake -S . -B build
  cmake --build build
  exit 0
fi

mapfile -t files < <(find . -type f -name '*.cpp' | sort)
if [[ ${#files[@]} -eq 0 ]]; then
  echo "cpp compile skipped: no .cpp files"
  exit 0
fi

mkdir -p build
g++ -std=c++20 -Wall -Wextra -pedantic "${files[@]}" -o build/cpp-smoke

