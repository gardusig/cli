#!/usr/bin/env bash
# Build PR and release Docker targets locally and compare key outputs.
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

root="$(gh_repo_root)"
cd "$root"

scratch="${COMPARE_SCRATCH:-/tmp/cli-docker-compare-$$}"
mkdir -p "$scratch"
trap 'rm -rf "$scratch"' EXIT

if ! command -v docker >/dev/null 2>&1; then
  echo "docker: command not found" >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "docker daemon not reachable (add your user to the docker group or run with sudo)" >&2
  exit 1
fi

version="$(gh_read_project_version "$root")"
base_version="${BASE_VERSION:-$(bash scripts/pull-request/host-last-published-version.sh 2>/dev/null || true)}"

echo "== compare-docker-pipelines =="
echo "project version: ${version}"
echo "base version:    ${base_version:-<none>}"
echo "PR dockerfile:   ${PR_DOCKERFILE}"
echo "release docker:  ${RELEASE_DOCKERFILE}"
echo "dockerignore:    ${DOCKERIGNORE}"
echo

_run_host() {
  echo "--- host: version-check ---"
  BASE_VERSION="${base_version}" bash scripts/pull-request/version-check.sh | tee "$scratch/host-version-check.log"
  echo "--- host: unit-test (summary) ---"
  bash scripts/pull-request/unit-test.sh 2>&1 | tee "$scratch/host-unit-test.log" | tail -5
}

_run_pr_docker() {
  echo "--- docker PR: version-check ---"
  DOCKERFILE="${PR_DOCKERFILE}" bash scripts/pull-request/build.sh version-check \
    --build-arg "BASE_VERSION=${base_version}" 2>&1 | tee "$scratch/pr-version-check.log"
  echo "--- docker PR: unit-test ---"
  DOCKERFILE="${PR_DOCKERFILE}" bash scripts/pull-request/build.sh unit-test 2>&1 | tee "$scratch/pr-unit-test.log" | tail -5
}

_compare_unit_summaries() {
  local host_line pr_line
  host_line="$(rg -o '[0-9]+ passed' "$scratch/host-unit-test.log" | tail -1 || true)"
  pr_line="$(rg -o '[0-9]+ passed' "$scratch/pr-unit-test.log" | tail -1 || true)"
  echo "--- compare unit-test ---"
  echo "host: ${host_line:-<no pytest summary>}"
  echo "PR docker: ${pr_line:-<no pytest summary>}"
  if [[ -n "$host_line" && -n "$pr_line" && "$host_line" != "$pr_line" ]]; then
    echo "MISMATCH: host and PR docker unit-test counts differ" >&2
    return 1
  fi
  if [[ -n "$host_line" && -n "$pr_line" ]]; then
    echo "OK: unit-test counts match (${host_line})"
  fi
}

_smoke_runtime_local() {
  echo "--- local venv cli --version (source install) ---"
  if [[ -x "${root}/.venv/bin/cli" ]]; then
    "${root}/.venv/bin/cli" --version | tee "$scratch/host-cli-version.log"
  else
    python3 -m src.cli --version | tee "$scratch/host-cli-version.log"
  fi
}

_smoke_release_runtime() {
  if [[ "${SKIP_RELEASE_DOCKER:-0}" == "1" ]]; then
    echo "--- skip release runtime (SKIP_RELEASE_DOCKER=1) ---"
    return 0
  fi
  echo "--- docker release: runtime image ---"
  if ! DOCKERFILE="${RELEASE_DOCKERFILE}" bash scripts/release/build.sh runtime \
    --build-arg "CLI_VERSION=${version}" \
    -t "cli-runtime-compare:${version}" 2>&1 | tee "$scratch/release-runtime-build.log"; then
    echo "note: release runtime build failed (package may not be on PyPI yet); set SKIP_RELEASE_DOCKER=1 to skip" >&2
    return 0
  fi
  docker run --rm "cli-runtime-compare:${version}" --version | tee "$scratch/release-runtime-version.log"
  echo "--- compare cli --version ---"
  echo "source/venv: $(cat "$scratch/host-cli-version.log")"
  echo "release img: $(cat "$scratch/release-runtime-version.log")"
}

_run_host
_run_pr_docker
_compare_unit_summaries
_smoke_runtime_local
_smoke_release_runtime

echo
echo "compare-docker-pipelines: done (logs in ${scratch})"
