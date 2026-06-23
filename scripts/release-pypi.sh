#!/usr/bin/env bash
# Build dist/ and upload gardusig-cli to PyPI (reads PYPI_API_TOKEN from .env).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=_common.sh
source "$ROOT/scripts/_common.sh"

require_pypi_token
export PYPI_API_TOKEN

echo "==> build"
"$ROOT/scripts/build-pypi.sh"

echo "==> publish"
"$ROOT/scripts/publish-pypi.sh" "$@"
