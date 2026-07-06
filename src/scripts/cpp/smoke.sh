#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

require_workspace
cd "$WORKSPACE"

if [[ -x build/cpp-smoke ]]; then
  ./build/cpp-smoke
else
  "$SCRIPTS_ROOT/cpp/compile.sh"
  [[ -x build/cpp-smoke ]] && ./build/cpp-smoke
fi

