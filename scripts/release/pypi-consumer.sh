#!/usr/bin/env bash
# Install gardusig-cli from PyPI and run post-publish integration smoke.
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

export PYPI_INDEX=pypi
stage_run_with_timeout "${CI_CONSUMER_TIMEOUT}" \
  bash "$(dirname "${BASH_SOURCE[0]}")/../pull-request/testpypi-consumer-body.sh"
