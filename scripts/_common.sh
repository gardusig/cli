#!/usr/bin/env bash
# Shared helpers for workflow wrappers and Docker stage scripts.
set -euo pipefail

# Stage timeouts — override via env (e.g. in workflow `env:` blocks).
: "${CI_UNIT_TIMEOUT:=5m}"
: "${CI_INTEGRATION_TIMEOUT:=3m}"
: "${CI_DOCKER_BUILD_TIMEOUT:=5m}"
: "${CI_VERSION_CHECK_TIMEOUT:=2m}"
: "${CI_TESTPYPI_TIMEOUT:=5m}"
: "${CI_CONSUMER_TIMEOUT:=5m}"
: "${CI_RESOLVE_TIMEOUT:=2m}"
: "${CI_LINT_TIMEOUT:=5m}"
: "${CI_RELEASE_SMOKE_TIMEOUT:=3m}"
: "${CI_DOCKER_PUSH_TIMEOUT:=5m}"

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

# Version / tag formats (all targets use bare semver X.Y.Z):
#   Git tag:     1.2.3
#   PyPI:        1.2.3
#   Docker Hub:  1.2.3  (+ :latest)
# Legacy tags may include a leading v; it is stripped before PyPI/Docker publish.
gh_strip_v_prefix() {
  local raw="${1:?version required}"
  echo "${raw#v}"
}

gh_set_project_version() {
  local root="${1:?root required}"
  local version
  version="$(gh_strip_v_prefix "${2:?version required}")"
  python3 - <<'PY' "$root" "$version"
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
version = sys.argv[2]
pyproject = root / "pyproject.toml"
init_py = root / "src" / "__init__.py"

text = pyproject.read_text(encoding="utf-8")
new_text, count = re.subn(
    r'^(version\s*=\s*")[^"]+(")',
    rf'\g<1>{version}\g<2>',
    text,
    count=1,
    flags=re.MULTILINE,
)
if count != 1:
    raise SystemExit("failed to update version in pyproject.toml")
pyproject.write_text(new_text, encoding="utf-8")

init_text = init_py.read_text(encoding="utf-8")
new_init, init_count = re.subn(
    r'^__version__\s*=\s*"[^"]+"',
    f'__version__ = "{version}"',
    init_text,
    count=1,
    flags=re.MULTILINE,
)
if init_count != 1:
    raise SystemExit("failed to update __version__ in src/__init__.py")
init_py.write_text(new_init, encoding="utf-8")
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
  local target="$1"
  shift
  local root dockerfile
  root="$(gh_repo_root)"
  dockerfile="${DOCKERFILE:-${PR_DOCKERFILE:-${RELEASE_DOCKERFILE:-}}}"
  if [[ -z "$dockerfile" ]]; then
    echo "DOCKERFILE required (PR_DOCKERFILE or RELEASE_DOCKERFILE)" >&2
    exit 1
  fi
  if [[ ! -f "${root}/${dockerfile}" ]]; then
    echo "dockerfile not found: ${root}/${dockerfile}" >&2
    exit 1
  fi
  docker build -f "${root}/${dockerfile}" --target "$target" "$@" "${root}"
}

export_cli_test_profile() {
  export CLI_PROFILE="${CLI_PROFILE:-test}"
}

stage_ensure_dev() {
  local root
  root="$(gh_repo_root)"
  export_cli_test_profile
  cd "$root"
  if command -v uv >/dev/null 2>&1 && [[ -f "${root}/uv.lock" ]]; then
    uv sync --group dev
    return
  fi
  local pip=(pip)
  if ! command -v pip >/dev/null 2>&1; then
    pip=(python3 -m pip)
  fi
  "${pip[@]}" install --no-cache-dir -e ".[dev]"
}

stage_ensure_test_deps() {
  stage_ensure_dev
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
  local runner=("$@")
  if ((${#runner[@]} >= 1)) && declare -F "${runner[0]}" >/dev/null 2>&1; then
    local fn="${runner[0]}"
    local args=()
    if ((${#runner[@]} > 1)); then
      args=("${runner[@]:1}")
    fi
    local quoted=""
    if ((${#args[@]} > 0)); then
      quoted="$(printf ' %q' "${args[@]}")"
    fi
    local common_sh
    common_sh="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"
    timeout --signal=TERM --kill-after=30s "$limit" bash -c "source $(printf '%q' "$common_sh"); $(declare -f "$fn"); $fn${quoted}"
    local code=$?
  else
    timeout --signal=TERM --kill-after=30s "$limit" "${runner[@]}"
    local code=$?
  fi
  if [[ "$code" -eq 0 ]]; then
    return 0
  fi
  if [[ "$code" -eq 124 ]]; then
    echo "timed out after ${limit}: ${runner[*]}" >&2
  fi
  return "$code"
}
