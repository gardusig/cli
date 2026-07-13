#!/usr/bin/env bash
# Shared helpers for workflow wrappers and Docker stage scripts.
set -euo pipefail

gh_repo_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd
}

PR_DOCKERFILE="${PR_DOCKERFILE:-docker/pull-request.dockerfile}"
RELEASE_DOCKERFILE="${RELEASE_DOCKERFILE:-docker/release.dockerfile}"
RUNTIME_IMAGE="${RUNTIME_IMAGE:-binarylifter/gardusig-cli}"

gh_read_project_version() {
  local root="${1:-$(gh_repo_root)}"
  python3 - <<'PY' "$root/pyproject.toml"
import sys
import tomllib

with open(sys.argv[1], "rb") as handle:
    print(tomllib.load(handle)["project"]["version"])
PY
}

gh_write_output() {
  local name="$1"
  local value="$2"
  if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
    echo "${name}=${value}" >> "$GITHUB_OUTPUT"
  else
    echo "${name}=${value}"
  fi
}

gh_docker_build() {
  local dockerfile="$1"
  local target="$2"
  shift 2
  local root
  root="$(gh_repo_root)"
  local ignorefile="${root}/docker/.dockerignore"
  local ignore_args=()
  if [[ -f "$ignorefile" ]]; then
    ignore_args=(--ignorefile "$ignorefile")
  fi
  docker build -f "$dockerfile" --target "$target" "${ignore_args[@]}" "$@" .
}

stage_ensure_dev() {
  local root
  root="$(gh_repo_root)"
  export CLI_CONFIG_DIR="${CLI_CONFIG_DIR:-${root}/config/ci}"
  cd "$root"
  pip install --no-cache-dir -r requirements-dev.txt
  pip install --no-cache-dir -e ".[dev]"
}

stage_ensure_test_deps() {
  local root
  root="$(gh_repo_root)"
  export CLI_CONFIG_DIR="${CLI_CONFIG_DIR:-${root}/config/ci}"
  cd "$root"
  pip install --no-cache-dir -r requirements-dev.txt
}

stage_compare_versions() {
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

stage_run_with_timeout() {
  local limit="$1"
  shift
  if ! command -v timeout >/dev/null 2>&1; then
    echo "timeout command not found (install coreutils)" >&2
    exit 1
  fi
  timeout --signal=TERM --kill-after=30s "$limit" "$@"
}
