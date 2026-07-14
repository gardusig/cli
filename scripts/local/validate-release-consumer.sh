#!/usr/bin/env bash
# Validate release TestPyPI consumer stage locally (matches release.yaml testpypi-consumer job).
# Usage:
#   bash scripts/local/validate-release-consumer.sh
#   PUBLISH_TESTPYPI=1 TESTPYPI_API_TOKEN=... bash scripts/local/validate-release-consumer.sh
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

root="$(gh_repo_root)"
cd "$root"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker: command not found" >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "docker daemon not reachable" >&2
  exit 1
fi

version="${CLI_RELEASE_VERSION:-$(gh_read_project_version "$root")}"
dockerfile="${RELEASE_DOCKERFILE:-docker/release.dockerfile}"

echo "== validate-release-consumer =="
echo "version:  ${version}"
echo "dockerfile: ${dockerfile}"
echo

if [[ "${PUBLISH_TESTPYPI:-0}" == "1" ]]; then
  if [[ -z "${TESTPYPI_API_TOKEN:-}" ]]; then
    echo "TESTPYPI_API_TOKEN is required when PUBLISH_TESTPYPI=1" >&2
    exit 1
  fi
  echo "--- docker build: testpypi ---"
  docker build -f "${dockerfile}" --target testpypi \
    --build-arg "CLI_RELEASE_VERSION=${version}" \
    --build-arg "TESTPYPI_API_TOKEN=${TESTPYPI_API_TOKEN}" .
else
  echo "--- skip testpypi publish (set PUBLISH_TESTPYPI=1 to upload first) ---"
fi

echo "--- docker build: testpypi-consumer ---"
docker build -f "${dockerfile}" --target testpypi-consumer \
  --build-arg "CLI_RELEASE_VERSION=${version}" .

echo
echo "validate-release-consumer: ok"
