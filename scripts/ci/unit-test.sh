#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/ci/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

ci_ensure_dev
ci_run_with_timeout "${CI_UNIT_TIMEOUT:-5m}" python3 -m pytest -q -m "not integration" \
  --cov=src \
  --cov-config=coverage-unit.ini \
  --cov-report=term-missing \
  --cov-fail-under=80
