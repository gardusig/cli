#!/usr/bin/env bash
# Tag release: PyPI publish (reads PYPI_API_TOKEN from .env).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$ROOT/scripts/release-pypi.sh" "$@"
