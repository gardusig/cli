#!/usr/bin/env bash
# Run all pack validation checks (delegates to ../tests/run.sh).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/../tests/run.sh"
