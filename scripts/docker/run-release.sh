#!/usr/bin/env bash
# PyPI release gate inside the cli:release container workdir (after copy).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if [[ -z "${PYPI_API_TOKEN:-}" ]]; then
  echo "ERROR: PYPI_API_TOKEN is not set (add to .env or export before release)." >&2
  exit 1
fi

export CLI_CONFIG_DIR="$ROOT/config/ci"
CLI_BOOTSTRAP_DEV=1 ./scripts/bootstrap.sh
# shellcheck disable=SC1091
source .venv/bin/activate

chmod +x scripts/pypi/*.sh
exec ./scripts/pypi/release.sh "$@"
