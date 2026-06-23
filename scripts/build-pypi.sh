#!/usr/bin/env bash
# Build PyPI sdist + wheel into dist/ (no upload).
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"
exec_cli publish pypi --build-only
