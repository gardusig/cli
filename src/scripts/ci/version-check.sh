#!/usr/bin/env bash
# PR gate: require pyproject version > base branch (this repo only).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
BASE_REF="${1:-origin/main}"
exec python -m src pypi version check --base "$BASE_REF"
