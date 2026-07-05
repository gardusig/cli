#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

require_workspace
cd "$WORKSPACE"

python3 -m pytest -q -m "not integration" \
  --cov=src \
  --cov-config=coverage-unit.ini \
  --cov-report=term-missing \
  --cov-fail-under=80

