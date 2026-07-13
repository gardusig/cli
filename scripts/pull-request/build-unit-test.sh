#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

bash "$(dirname "${BASH_SOURCE[0]}")/build.sh" unit-test
