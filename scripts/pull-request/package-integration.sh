#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

package="${PACKAGE:-cli}"
stage_ensure_dev
export CLI_DOCKER_INTEGRATION=1
export CLI_ROOT="$(gh_repo_root)"
export CLI_CONFIG_DIR="${CLI_CONFIG_DIR:-${CLI_ROOT}/config/ci}"

# shellcheck source=scripts/test/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../test/_common.sh"
run_package "$package" --no-unit "$@"
