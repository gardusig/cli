#!/usr/bin/env bash
# Build gardusig-cli sdist + wheel (no upload).
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"

args=()
if [[ -n "${CLI_RELEASE_VERSION:-}" ]]; then
  args+=(--version "$CLI_RELEASE_VERSION")
fi
if [[ -n "${CLI_DIST_DIR:-}" ]]; then
  args+=(--dist-dir "$CLI_DIST_DIR")
fi
exec_cli pypi build "${args[@]}" "$@"
