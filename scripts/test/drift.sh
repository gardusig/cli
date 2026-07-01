#!/usr/bin/env bash
# Version / drift gate — run at start of integration phase on PRs.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [[ -f "$ROOT/pyproject.toml" ]] && command -v python3 >/dev/null 2>&1; then
  BASE="${GITHUB_BASE_REF:-origin/main}"
  if git rev-parse "$BASE" >/dev/null 2>&1; then
    echo "==> version drift check (HEAD vs ${BASE})"
    python3 -m src pypi version check --base "$BASE" 2>/dev/null || {
      echo "WARN: version check skipped (install cli or use Docker integration gate)" >&2
    }
  else
    echo "==> version drift check skipped (base ref ${BASE} not found)"
  fi
elif [[ -x "$ROOT/scripts/ci/version-check.sh" ]]; then
  BASE="${GITHUB_BASE_REF:-origin/main}"
  echo "==> version drift check via scripts/ci/version-check.sh"
  ./scripts/ci/version-check.sh "$BASE" || true
else
  echo "==> no version manifest in repo — drift check skipped"
fi
