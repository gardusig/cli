#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/ci/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

ci_ensure_dev
export CLI_DOCKER_INTEGRATION=1
export CLI_ROOT="$(ci_repo_root)"

python3 tests/integration/check_integration_coverage.py
python3 tests/integration/check_public_commands.py
python3 tests/integration/check_workflow_integration.py
python3 tests/integration/check_api_integration.py
python -m pytest -q -m integration
