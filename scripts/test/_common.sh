#!/usr/bin/env bash
# Shared helpers for per-package test scripts (Epic 00).
set -euo pipefail

repo_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd
}

run_package() {
  local package="$1"
  shift
  local root
  root="$(repo_root)"
  export CLI_CONFIG_DIR="${CLI_CONFIG_DIR:-config/ci}"
  cd "$root"
  exec python3 -m src test packages run "$package" --path "$root" "$@"
}
