#!/usr/bin/env bash
# Sequential PR test pipeline — unit → integration (drift) → regression → PyPI smoke.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
chmod +x scripts/test/*.sh scripts/docker/*.sh 2>/dev/null || true

echo "==> [1/4] unit tests (Docker)"
./scripts/test/unit.sh

echo "==> [2/4] integration tests + version drift (Docker)"
./scripts/test/integration.sh

echo "==> [3/4] regression tests (Docker)"
./scripts/test/regression.sh

echo "==> [4/4] PyPI packaging smoke (Docker)"
./scripts/test/pypi.sh

echo "==> test pipeline passed"
