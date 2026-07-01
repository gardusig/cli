#!/usr/bin/env bash
# PyPI test packaging smoke (runs in pypi-test container).
set -euo pipefail
if [[ "${CLI_DOCKER_INTEGRATION:-}" != "1" ]]; then
  echo "ERROR: run via ./scripts/test/pypi.sh" >&2
  exit 1
fi
cd /app
export CLI_CONFIG_DIR=/app/config/ci
CLI_BOOTSTRAP_DEV=1 ./scripts/docker/bootstrap.sh
source .venv/bin/activate
chmod +x scripts/pypi/*.sh
export CLI_PYPI_TEST_VERSION="${CLI_PYPI_TEST_VERSION:-1.0.0}"
./scripts/pypi/test.sh
