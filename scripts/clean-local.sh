#!/usr/bin/env bash
# Remove local build/test artifacts (safe: does not touch .env or source).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

remove_if_exists() {
  local path="$1"
  if [[ -e "$path" ]]; then
    rm -rf "$path"
    echo "removed $path"
  fi
}

remove_if_exists dist
remove_if_exists build
remove_if_exists .integration-scratch
remove_if_exists .pytest_cache
remove_if_exists .coverage
remove_if_exists coverage.xml
remove_if_exists htmlcov
remove_if_exists gardusig_cli.egg-info

shopt -s nullglob
for path in gardusig_cli-*/; do
  remove_if_exists "$path"
done
for pattern in cli-git-* cli-public-* cli-workflow-* cli-tag-zip-* cli-outside-git-* cli-contest-*; do
  for path in $pattern/; do
    remove_if_exists "$path"
  done
  for path in ${pattern}-origin.git/; do
    remove_if_exists "$path"
  done
done
shopt -u nullglob

find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true

echo "clean-local done"
