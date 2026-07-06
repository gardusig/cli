#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

require_workspace
cd "$WORKSPACE"

python3 tests/integration/check_integration_coverage.py
python3 tests/integration/check_public_commands.py
python3 tests/integration/check_workflow_integration.py
python3 tests/integration/check_api_integration.py
python3 -m pytest -q -m integration

