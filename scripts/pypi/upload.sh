#!/usr/bin/env bash
# Build and upload gardusig-cli (requires PYPI_API_TOKEN).
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"

require_pypi_token
export PYPI_API_TOKEN

args=(--yes)
if [[ -n "${CLI_RELEASE_VERSION:-}" ]]; then
  args+=(--version "$CLI_RELEASE_VERSION")
fi
if [[ -n "${CLI_DIST_DIR:-}" ]]; then
  args+=(--dist-dir "$CLI_DIST_DIR")
fi
if [[ "${CLI_PYPI_TEST:-0}" == "1" ]]; then
  args+=(--testpypi)
fi
if [[ "${CLI_PYPI_SKIP_EXISTING:-0}" == "1" ]]; then
  args+=(--skip-existing)
fi
exec_cli pypi upload "${args[@]}" "$@"
