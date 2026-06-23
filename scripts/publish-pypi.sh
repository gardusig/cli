#!/usr/bin/env bash
# Build and upload gardusig-cli to PyPI (requires PYPI_API_TOKEN in .env or env).
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
require_pypi_token
export PYPI_API_TOKEN
exec_cli publish pypi --yes "$@"
