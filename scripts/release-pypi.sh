#!/usr/bin/env bash
# Deprecated — use scripts/release.sh (see docs/release.md)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$ROOT/scripts/release.sh" "$@"
