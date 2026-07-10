#!/usr/bin/env bash
# Integration suite against the pip-installed package from TestPyPI (no editable install).
set -euo pipefail
# shellcheck source=scripts/ci/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

export CLI_DOCKER_INTEGRATION=1
export CLI_ROOT="$(ci_repo_root)"
export CLI_CONFIG_DIR="${CLI_CONFIG_DIR:-${CLI_ROOT}/config/ci}"

ci_ensure_test_deps

ci_run_with_timeout "${CI_INTEGRATION_TIMEOUT:-10m}" bash -c '
set -euo pipefail
python3 tests/integration/check_integration_coverage.py
python3 tests/integration/check_public_commands.py
python3 tests/integration/check_workflow_integration.py
python3 tests/integration/check_api_integration.py
python -m pytest -q -m integration
'
