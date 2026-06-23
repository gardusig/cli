#!/usr/bin/env bash
# Unit test gate inside the container workdir (after copy + git init).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export CLI_CONFIG_DIR="$ROOT/config/ci"
CLI_BOOTSTRAP_DEV=1 ./scripts/bootstrap.sh
source .venv/bin/activate
bash -n scripts/chrome/*.sh
bash -n scripts/docker/*.sh
python tests/integration/check_integration_coverage.py
pytest -q \
  --cov=cli \
  --cov-config=coverage-unit.ini \
  --cov-report=term-missing \
  --cov-fail-under=80
