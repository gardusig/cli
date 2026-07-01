#!/usr/bin/env bash
# Unit test gate inside the container workdir (after copy + git init).
set -euo pipefail
if [[ "${CLI_DOCKER_INTEGRATION:-}" != "1" ]]; then
  echo "ERROR: run via ./scripts/test/unit.sh (Docker integration image), not on the host." >&2
  exit 1
fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export CLI_CONFIG_DIR="$ROOT/config/ci"
if [[ ! -d .git ]]; then
  git init -b main >/dev/null
  git config user.email "cli@example.test"
  git config user.name "Cli Docker Unit"
  git add pyproject.toml README.md src scripts tests config/ci
  git commit -m "docker unit snapshot" >/dev/null
fi
CLI_BOOTSTRAP_DEV=1 ./scripts/docker/bootstrap.sh
source .venv/bin/activate
bash -n scripts/chrome/*.sh
bash -n scripts/docker/*.sh
python tests/integration/check_integration_coverage.py
pytest -q -m "not integration" \
  --cov=src \
  --cov-config=coverage-unit.ini \
  --cov-report=term-missing \
  --cov-fail-under=80
