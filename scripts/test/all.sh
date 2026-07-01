#!/usr/bin/env bash
# Sequential PR test pipeline — same order as .github/workflows/test.yml
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
chmod +x scripts/test/*.sh scripts/docker/*.sh 2>/dev/null || true

echo "==> [1/4] version check (Docker)"
./scripts/test/version.sh

echo "==> [2/4] unit tests (Docker)"
./scripts/test/unit.sh

echo "==> [3/4] integration tests (Docker)"
./scripts/test/integration.sh

echo "==> [4/4] PyPI packaging smoke (Docker)"
./scripts/test/pypi.sh

echo "==> test pipeline passed"
