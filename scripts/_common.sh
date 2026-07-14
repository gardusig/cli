#!/usr/bin/env bash
# Shared helpers for workflow wrappers and Docker stage scripts.
set -euo pipefail

# Stage timeouts — override via env (e.g. in workflow `env:` blocks).
: "${CI_UNIT_TIMEOUT:=5m}"
: "${CI_INTEGRATION_TIMEOUT:=3m}"
: "${CI_DOCKER_BUILD_TIMEOUT:=5m}"
: "${CI_VERSION_CHECK_TIMEOUT:=2m}"
: "${CI_TESTPYPI_TIMEOUT:=5m}"
: "${CI_CONSUMER_TIMEOUT:=10m}"
: "${CI_RESOLVE_TIMEOUT:=2m}"
: "${CI_LINT_TIMEOUT:=5m}"
: "${CI_RELEASE_SMOKE_TIMEOUT:=3m}"
: "${CI_DOCKER_PUSH_TIMEOUT:=5m}"
: "${CI_RUNTIME_INSTALL_TIMEOUT:=10m}"
: "${PIP_INSTALL_ATTEMPTS:=12}"
: "${PIP_INSTALL_INITIAL_DELAY:=4}"
: "${PIP_INSTALL_BACKOFF_MULTIPLIER:=2}"
: "${PIP_INSTALL_MAX_DELAY:=45}"
: "${PYPI_INDEX_SETTLE_SECONDS:=0}"
: "${DOCKER_REGISTRY_SETTLE_SECONDS:=0}"
: "${DOCKER_PULL_ATTEMPTS:=12}"
: "${DOCKER_PULL_INITIAL_DELAY:=4}"
: "${DOCKER_PULL_BACKOFF_MULTIPLIER:=2}"
: "${DOCKER_PULL_MAX_DELAY:=45}"

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

pypi_backoff_seconds() {
  local attempt="$1"
  python3 - <<'PY' "$attempt" "${PIP_INSTALL_INITIAL_DELAY}" "${PIP_INSTALL_BACKOFF_MULTIPLIER}" "${PIP_INSTALL_MAX_DELAY}"
import math
import sys

attempt = int(sys.argv[1])
initial = float(sys.argv[2])
multiplier = float(sys.argv[3])
cap = float(sys.argv[4])
delay = min(initial * (multiplier ** max(0, attempt - 1)), cap)
print(int(math.ceil(delay)))
PY
}

pypi_registry_backoff_seconds() {
  pypi_backoff_seconds "$1"
}

docker_registry_backoff_seconds() {
  local attempt="$1"
  python3 - <<'PY' "$attempt" "${DOCKER_PULL_INITIAL_DELAY}" "${DOCKER_PULL_BACKOFF_MULTIPLIER}" "${DOCKER_PULL_MAX_DELAY}"
import math
import sys

attempt = int(sys.argv[1])
initial = float(sys.argv[2])
multiplier = float(sys.argv[3])
cap = float(sys.argv[4])
delay = min(initial * (multiplier ** max(0, attempt - 1)), cap)
print(int(math.ceil(delay)))
PY
}

pypi_settle_before_pull() {
  local package="$1"
  local version="$2"
  local index="${3:-pypi}"
  local settle="${PYPI_INDEX_SETTLE_SECONDS}"
  if (( settle > 0 )); then
    echo "settling ${settle}s before checking ${package}==${version} on ${index}..."
    sleep "$settle"
  fi
}

pypi_index_has_version() {
  local package="$1"
  local version="$2"
  local index="${3:-pypi}"
  local url
  if [[ "$index" == "pypi" ]]; then
    url="https://pypi.org/pypi/${package}/json"
  else
    url="https://test.pypi.org/pypi/${package}/json"
  fi
  local response
  response="$(curl -fsS "$url" 2>/dev/null || true)"
  [[ -n "$response" ]] && printf '%s' "$response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
version = sys.argv[1]
files = (data.get('releases') or {}).get(version) or []
sys.exit(0 if files else 1)
" "$version"
}

pypi_pip_install_args() {
  local package="$1"
  local version="$2"
  local index="${3:-pypi}"
  if [[ "$index" == "pypi" ]]; then
    printf '%s\0' pip install --no-cache-dir "${package}==${version}"
  else
    printf '%s\0' pip install --no-cache-dir \
      --index-url https://test.pypi.org/simple/ \
      --extra-index-url https://pypi.org/simple/ \
      "${package}==${version}"
  fi
}

# Wait for index propagation, then pip install, with exponential backoff between attempts.
pypi_wait_and_install_package() {
  local package="${1:-gardusig-cli}"
  local version="${2:?version required}"
  local index="${3:-pypi}"
  local attempts="${PIP_INSTALL_ATTEMPTS}"
  local attempt=1
  local -a pip_args=()

  pypi_settle_before_pull "$package" "$version" "$index"

  while (( attempt <= attempts )); do
    if pypi_index_has_version "$package" "$version" "$index"; then
      mapfile -d '' -t pip_args < <(pypi_pip_install_args "$package" "$version" "$index")
      if "${pip_args[@]}"; then
        echo "installed ${package}==${version} from ${index}"
        return 0
      fi
      echo "index lists ${package}==${version} on ${index} but pip install failed (${attempt}/${attempts})"
    else
      echo "waiting for ${package}==${version} on ${index} (${attempt}/${attempts})..."
    fi
    if (( attempt < attempts )); then
      local delay
      delay="$(pypi_backoff_seconds "$attempt")"
      echo "retrying in ${delay}s..."
      sleep "$delay"
    fi
    attempt=$((attempt + 1))
  done
  echo "failed to install ${package}==${version} from ${index} after ${attempts} attempts" >&2
  return 1
}

docker_registry_has_tag() {
  local image="${1:?image required}"
  local tag="${2:?tag required}"
  curl -fsS "https://hub.docker.com/v2/repositories/${image}/tags/${tag}/" >/dev/null 2>&1
}

docker_settle_before_pull() {
  local image="$1"
  local tag="$2"
  local settle="${DOCKER_REGISTRY_SETTLE_SECONDS}"
  if (( settle > 0 )); then
    echo "settling ${settle}s before checking ${image}:${tag} on Docker Hub..."
    sleep "$settle"
  fi
}

# Wait for Docker Hub tag propagation, then pull, with exponential backoff between attempts.
docker_wait_and_pull() {
  local image="${1:?image required}"
  local tag="${2:?tag required}"
  local attempts="${DOCKER_PULL_ATTEMPTS}"
  local attempt=1

  docker_settle_before_pull "$image" "$tag"

  while (( attempt <= attempts )); do
    if docker_registry_has_tag "$image" "$tag"; then
      if docker pull "${image}:${tag}"; then
        echo "pulled ${image}:${tag} from Docker Hub"
        return 0
      fi
      echo "registry lists ${image}:${tag} but docker pull failed (${attempt}/${attempts})"
    else
      echo "waiting for ${image}:${tag} on Docker Hub (${attempt}/${attempts})..."
    fi
    if (( attempt < attempts )); then
      local delay
      delay="$(docker_registry_backoff_seconds "$attempt")"
      echo "retrying in ${delay}s..."
      sleep "$delay"
    fi
    attempt=$((attempt + 1))
  done
  echo "failed to pull ${image}:${tag} from Docker Hub after ${attempts} attempts" >&2
  return 1
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
