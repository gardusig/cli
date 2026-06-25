#!/usr/bin/env bash
# Full test gate: tag/zip unit (host) + Docker unit + integration.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "==> [1/4] tag / zip / version (host pytest)"
./scripts/test/tags.sh

echo "==> [2/4] workflow E2E (host pytest, mocked gh)"
./scripts/test/workflows.sh

echo "==> [3/4] unit tests (Docker)"
./scripts/test/unit.sh

echo "==> [4/4] integration tests (Docker)"
./scripts/test/integration.sh

echo "==> all tests passed"
