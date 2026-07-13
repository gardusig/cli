#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

stage_ensure_dev
export CLI_DOCKER_INTEGRATION=1
export CLI_ROOT="$(gh_repo_root)"
python3 tests/integration/check_public_commands.py
