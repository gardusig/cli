#!/usr/bin/env bash
# Shared Docker harness — build a Dockerfile target and run it (local + CI).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DOCKERFILE="${REPO_DOCKERFILE:-$REPO_ROOT/Dockerfile}"
UNIT_TIMEOUT_SEC="${REPO_UNIT_TIMEOUT_SEC:-120}"
INTEGRATION_TIMEOUT_SEC="${REPO_INTEGRATION_TIMEOUT_SEC:-480}"
DEPLOY_TIMEOUT_SEC="${REPO_DEPLOY_TIMEOUT_SEC:-600}"
RELEASE_TIMEOUT_SEC="${REPO_RELEASE_TIMEOUT_SEC:-900}"

docker_require() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker is not installed or not on PATH" >&2
    exit 127
  fi
  if ! command -v timeout >/dev/null 2>&1; then
    echo "ERROR: timeout(1) is required (coreutils)" >&2
    exit 127
  fi
}

docker_image_for() {
  local target="$1"
  printf '%s\n' "${REPO_DOCKER_IMAGE:-$(basename "$REPO_ROOT"):$(basename "$target")}"
}

docker_build_target() {
  local target="$1"
  local image
  image="$(docker_image_for "$target")"
  echo "==> docker build --target ${target} -t ${image}"
  docker build -f "$DOCKERFILE" --target "$target" -t "$image" "$REPO_ROOT"
}

docker_run_args() {
  local -a args=()
  if [[ "${REPO_DOCKER_SOCKET:-0}" == "1" ]]; then
    if [[ ! -S /var/run/docker.sock ]]; then
      echo "ERROR: /var/run/docker.sock not found" >&2
      exit 1
    fi
    args+=(-v /var/run/docker.sock:/var/run/docker.sock)
  fi
  printf '%s\0' "${args[@]}"
}

docker_run_target() {
  local target="$1"
  local timeout_sec="$2"
  local image
  image="$(docker_image_for "$target")"
  docker_build_target "$target"
  echo "==> docker run (timeout ${timeout_sec}s): ${image}"
  local -a run_args=()
  if [[ "${REPO_DOCKER_SOCKET:-0}" == "1" ]]; then
    run_args+=(-v /var/run/docker.sock:/var/run/docker.sock)
  fi
  timeout "$timeout_sec" docker run --rm "${run_args[@]}" "$image"
}

docker_run_target_with_repo() {
  local target="$1"
  local timeout_sec="$2"
  local image
  image="$(docker_image_for "$target")"
  docker_build_target "$target"
  echo "==> docker run with repo mount (timeout ${timeout_sec}s): ${image}"
  local -a run_args=(
    -v "${REPO_ROOT}:/repo:rw"
    -w /repo
    -e GH_TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
    -e GITHUB_TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
    -e GITHUB_REF_NAME="${GITHUB_REF_NAME:-}"
    -e GITHUB_BASE_REF="${GITHUB_BASE_REF:-main}"
  )
  if [[ "${REPO_DOCKER_SOCKET:-0}" == "1" ]]; then
    run_args+=(-v /var/run/docker.sock:/var/run/docker.sock)
  fi
  timeout "$timeout_sec" docker run --rm "${run_args[@]}" "$image"
}

docker_run_target_with_artifacts() {
  local target="$1"
  local timeout_sec="$2"
  local image
  image="$(docker_image_for "$target")"
  mkdir -p "${REPO_ROOT}/artifacts"
  docker_build_target "$target"
  echo "==> docker run with artifacts mount (timeout ${timeout_sec}s): ${image}"
  timeout "$timeout_sec" docker run --rm \
    -v "${REPO_ROOT}:/repo:ro" \
    -v "${REPO_ROOT}/artifacts:/artifacts:rw" \
    -e GITHUB_REF_NAME="${GITHUB_REF_NAME:-}" \
    "$image"
}

run_unit_tests() {
  docker_require
  docker_run_target unit "$UNIT_TIMEOUT_SEC"
}

run_integration_tests() {
  docker_require
  docker_run_target integration "$INTEGRATION_TIMEOUT_SEC"
}

run_deploy() {
  docker_require
  docker_run_target_with_repo deploy "$DEPLOY_TIMEOUT_SEC"
}

run_release_build() {
  docker_require
  docker_run_target_with_artifacts release "$RELEASE_TIMEOUT_SEC"
}
