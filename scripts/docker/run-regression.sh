#!/usr/bin/env bash
# Regression gate — pack tests + workflow smoke (no live external services).
set -euo pipefail
if [[ "${CLI_DOCKER_INTEGRATION:-}" != "1" ]]; then
  echo "ERROR: run via ./scripts/test/regression.sh (Docker regression image)" >&2
  exit 1
fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export CLI_CONFIG_DIR="$ROOT/config/ci"
CLI_BOOTSTRAP_DEV=1 ./scripts/docker/bootstrap.sh
source .venv/bin/activate

run_step() {
  echo "==> $1"
  shift
  "$@"
}

run_step "pack regression" pytest -q tests/pack tests/opencode tests/gh/test_merge_forbidden.py tests/gh/test_projects_and_organize.py tests/services/test_gh_topo.py tests/services/test_chat_session.py tests/services/test_chat_distill.py tests/services/test_craft_ai.py
run_step "workflow regression" python tests/integration/check_workflows.py
