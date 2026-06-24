#!/usr/bin/env bash
# Deprecated — use scripts/pypi/upload.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$ROOT/scripts/pypi/upload.sh" "$@"
