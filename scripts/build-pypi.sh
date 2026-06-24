#!/usr/bin/env bash
# Deprecated — use scripts/pypi/build.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$ROOT/scripts/pypi/build.sh" "$@"
