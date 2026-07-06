#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

require_workspace
cd "$WORKSPACE"

tool=$(java_build_tool)
if [[ "$tool" == "mvn" ]]; then
  mvn -q test
else
  "$tool" test --no-daemon
fi

