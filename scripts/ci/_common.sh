#!/usr/bin/env bash
# Shared helpers for CI stage scripts (raw shell — no cli command, no python3 -m src).
set -euo pipefail

ci_repo_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd
}

ci_ensure_dev() {
  local root
  root="$(ci_repo_root)"
  export CLI_CONFIG_DIR="${CLI_CONFIG_DIR:-${root}/config/ci}"
  cd "$root"
  pip install --no-cache-dir -r requirements-dev.txt
  pip install --no-cache-dir -e ".[dev]"
}

ci_ensure_test_deps() {
  local root
  root="$(ci_repo_root)"
  export CLI_CONFIG_DIR="${CLI_CONFIG_DIR:-${root}/config/ci}"
  cd "$root"
  pip install --no-cache-dir -r requirements-dev.txt
}

ci_read_project_version() {
  local root="${1:-$(ci_repo_root)}"
  python3 - <<'PY' "$root/pyproject.toml"
import sys
import tomllib

with open(sys.argv[1], "rb") as handle:
    print(tomllib.load(handle)["project"]["version"])
PY
}

ci_compare_versions() {
  # Prints ok when head > base; exits 1 otherwise.
  local base="$1"
  local head="$2"
  python3 - <<'PY' "$base" "$head"
import sys

def parse(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for piece in version.strip().lstrip("v").split("."):
        digits = ""
        for char in piece:
            if char.isdigit():
                digits += char
            else:
                break
        parts.append(int(digits or "0"))
    return tuple(parts)

base = parse(sys.argv[1])
head = parse(sys.argv[2])
if head <= base:
    raise SystemExit(
        f"version {sys.argv[2]!r} is not greater than {sys.argv[1]!r}"
    )
print(f"version ok: {sys.argv[2]} > {sys.argv[1]}")
PY
}

ci_run_with_timeout() {
  local limit="$1"
  shift
  if ! command -v timeout >/dev/null 2>&1; then
    echo "timeout command not found (install coreutils)" >&2
    exit 1
  fi
  timeout --signal=TERM --kill-after=30s "$limit" "$@"
}
