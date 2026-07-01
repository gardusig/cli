#!/usr/bin/env bash
# Version gate — pyproject version must exceed base branch (runs in version container).
set -euo pipefail
cd /repo
git config --global --add safe.directory /repo
pip install --quiet -e .
base="${GITHUB_BASE_REF:-main}"
git fetch origin "${base}" 2>/dev/null || git fetch origin "main" 2>/dev/null || true
chmod +x scripts/ci/version-check.sh
./scripts/ci/version-check.sh "origin/${base}"
