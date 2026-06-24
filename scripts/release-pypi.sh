#!/usr/bin/env bash
# Deprecated — use scripts/pypi/release.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$ROOT/scripts/pypi/release.sh" "$@"
