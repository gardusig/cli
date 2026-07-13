#!/usr/bin/env bash
# Integration suite against the pip-installed package from TestPyPI (no editable install).
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"
# shellcheck source=scripts/pull-request/consumer/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/consumer/_common.sh"

stage_ensure_test_deps
consumer_install_package

stage_run_with_timeout "${CI_INTEGRATION_TIMEOUT}" bash scripts/pull-request/integration-smoke.sh
