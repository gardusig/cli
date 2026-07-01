#!/usr/bin/env bash
# Integration gate inside the container workdir (pytest + smoke + live docker).
set -euo pipefail
if [[ "${CLI_DOCKER_INTEGRATION:-}" != "1" ]]; then
  echo "ERROR: run via ./scripts/test/integration.sh (Docker integration image), not on the host." >&2
  exit 1
fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export CLI_CONFIG_DIR="$ROOT/config/ci"
if [[ ! -d .git ]]; then
  git init -b main >/dev/null
  git config user.email "cli@example.test"
  git config user.name "Cli Docker Integration"
  git add pyproject.toml README.md src scripts tests config/ci
  git commit -m "docker integration snapshot" >/dev/null
fi
CLI_BOOTSTRAP_DEV=1 ./scripts/docker/bootstrap.sh
source .venv/bin/activate

run_step() {
  echo "==> $1"
  shift
  "$@"
}

run_step "pytest" pytest -q
run_step "integration smoke" ./scripts/test/smoke.sh
run_step "live docker checks" python tests/integration/check_docker_commands.py --live
