#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

stage_ensure_dev
export CLI_DOCKER_INTEGRATION=1
export CLI_ROOT="$(gh_repo_root)"

stage_run_with_timeout "${CI_INTEGRATION_TIMEOUT:-10m}" bash -c '
set -euo pipefail
python3 tests/integration/check_integration_coverage.py
python3 tests/integration/check_public_commands.py
python3 tests/integration/check_workflow_integration.py
python3 tests/integration/check_api_integration.py
python -m pytest -q -m integration
'
