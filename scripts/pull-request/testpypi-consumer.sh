#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

stage_run_with_timeout "${CI_CONSUMER_TIMEOUT}" bash "$(dirname "${BASH_SOURCE[0]}")/testpypi-consumer-body.sh" "$@"
