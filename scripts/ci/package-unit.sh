#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/test/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../test/_common.sh"

package="${PACKAGE:-cli}"
run_package "$package" --no-integration "$@"
