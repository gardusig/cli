#!/usr/bin/env bash
# Local preview of .github/workflows/release.yaml (dry-run by default).
#
# Default (no uploads):
#   resolve → testpypi-consumer → build runtime image locally
#
# Optional uploads (set to 1):
#   PUBLISH_TESTPYPI=1 TESTPYPI_API_TOKEN=...
#   PUBLISH_PYPI=1 PYPI_API_TOKEN=...
#   PUBLISH_DOCKER=1   (docker login must already work on host)
#   PUBLISH_GITHUB=1 GH_TOKEN=... GITHUB_REPOSITORY=owner/repo RELEASE_TAG=X.Y.Z
#
# Examples:
#   bash scripts/local/preview-release-workflow.sh
#   GITHUB_REF_NAME=1.1.3 bash scripts/local/preview-release-workflow.sh
#   PUBLISH_TESTPYPI=1 TESTPYPI_API_TOKEN=... bash scripts/local/preview-release-workflow.sh
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

dockerfile="${RELEASE_DOCKERFILE:-docker/release.dockerfile}"
runtime_image="${RUNTIME_IMAGE:-binarylifter/gardusig-cli}"
project_version="$(gh_read_project_version "$root")"
tag="${GITHUB_REF_NAME:-${RELEASE_TAG:-$project_version}}"
local_runtime_tag="cli-release-preview:${tag}"

_publish_flag() {
  [[ "${1:-0}" == "1" ]]
}

_read_github_output() {
  local file="$1"
  local key="$2"
  sed -n "s/^${key}=//p" "$file" | head -1
}

_pypi_has_version() {
  local version="$1"
  local index="${2:-pypi}"
  local url
  if [[ "$index" == "testpypi" ]]; then
    url="https://test.pypi.org/pypi/gardusig-cli/json"
  else
    url="https://pypi.org/pypi/gardusig-cli/json"
  fi
  curl -fsS "$url" | python3 -c "
import json, sys
data = json.load(sys.stdin)
version = sys.argv[1]
files = (data.get('releases') or {}).get(version) or []
sys.exit(0 if files else 1)
" "$version"
}

echo "== preview-release-workflow =="
echo "dockerfile:     ${dockerfile}"
echo "tag:            ${tag}"
echo "project:        ${project_version}"
echo "runtime image:  ${runtime_image}"
echo "PUBLISH_TESTPYPI=${PUBLISH_TESTPYPI:-0}"
echo "PUBLISH_PYPI=${PUBLISH_PYPI:-0}"
echo "PUBLISH_DOCKER=${PUBLISH_DOCKER:-0}"
echo "PUBLISH_GITHUB=${PUBLISH_GITHUB:-0}"
echo

resolve_out="$(mktemp)"
trap 'rm -f "$resolve_out"' EXIT

echo "--- resolve ---"
docker build -f "${dockerfile}" --target resolve -t ci-release-resolve .
docker run --rm \
  -e GITHUB_OUTPUT=/out \
  -e GITHUB_REF_NAME="${tag}" \
  -v "${resolve_out}:/out" \
  ci-release-resolve

version="$(_read_github_output "$resolve_out" version)"
git_tag="$(_read_github_output "$resolve_out" git_tag)"
docker_tag="$(_read_github_output "$resolve_out" docker_tag)"
version="${version:-$project_version}"
git_tag="${git_tag:-$tag}"
docker_tag="${docker_tag:-$version}"

echo "resolved version=${version} git_tag=${git_tag} docker_tag=${docker_tag}"
echo

if _publish_flag "${PUBLISH_TESTPYPI:-0}"; then
  echo "--- publish-testpypi ---"
  if [[ -z "${TESTPYPI_API_TOKEN:-}" ]]; then
    echo "TESTPYPI_API_TOKEN is required when PUBLISH_TESTPYPI=1" >&2
    exit 1
  fi
  docker build -f "${dockerfile}" --target testpypi \
    --build-arg "CLI_RELEASE_VERSION=${version}" \
    --build-arg "TESTPYPI_API_TOKEN=${TESTPYPI_API_TOKEN}" .
else
  echo "--- publish-testpypi (skipped; set PUBLISH_TESTPYPI=1 to upload) ---"
fi
echo

echo "--- testpypi-consumer ---"
docker build -f "${dockerfile}" --target testpypi-consumer \
  --build-arg "CLI_RELEASE_VERSION=${version}" .
echo

if _publish_flag "${PUBLISH_PYPI:-0}"; then
  echo "--- publish-pypi ---"
  if [[ -z "${PYPI_API_TOKEN:-}" ]]; then
    echo "PYPI_API_TOKEN is required when PUBLISH_PYPI=1" >&2
    exit 1
  fi
  docker build -f "${dockerfile}" --target pypi \
    --build-arg "CLI_RELEASE_VERSION=${version}" \
    --build-arg "PYPI_API_TOKEN=${PYPI_API_TOKEN}" .
else
  echo "--- publish-pypi (skipped; set PUBLISH_PYPI=1 to upload) ---"
fi
echo

echo "--- pypi-consumer ---"
if _publish_flag "${PUBLISH_PYPI:-0}" || _pypi_has_version "${docker_tag}" pypi; then
  docker build -f "${dockerfile}" --target pypi-consumer \
    --build-arg "CLI_RELEASE_VERSION=${docker_tag}" .
else
  echo "skip pypi-consumer (gardusig-cli==${docker_tag} not on PyPI; set PUBLISH_PYPI=1 first)"
fi
echo

echo "--- publish-docker — build runtime ---"
if _publish_flag "${PUBLISH_PYPI:-0}"; then
  docker build -f "${dockerfile}" --target runtime \
    --build-arg "CLI_VERSION=${docker_tag}" \
    -t "${runtime_image}:${docker_tag}" \
    -t "${runtime_image}:latest" .
elif _pypi_has_version "${docker_tag}" pypi; then
  docker build -f "${dockerfile}" --target runtime \
    --build-arg "CLI_VERSION=${docker_tag}" \
    -t "${local_runtime_tag}" .
  echo "local preview tag: ${local_runtime_tag}"
  docker run --rm "${local_runtime_tag}" --version
else
  echo "skip runtime build (gardusig-cli==${docker_tag} not on PyPI; set PUBLISH_PYPI=1 first)"
fi
echo

if _publish_flag "${PUBLISH_DOCKER:-0}"; then
  echo "--- publish-docker — push + smoke ---"
  docker build -f "${dockerfile}" --target ci-push -t ci-release-push .
  docker build -f "${dockerfile}" --target ci-smoke -t ci-release-smoke .
  docker run --rm \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -e CLI_VERSION="${docker_tag}" \
    -e RUNTIME_IMAGE="${runtime_image}" \
    ci-release-push
  docker run --rm \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -e CLI_VERSION="${docker_tag}" \
    -e RUNTIME_IMAGE="${runtime_image}" \
    ci-release-smoke
else
  echo "--- publish-docker push/smoke (skipped; set PUBLISH_DOCKER=1 after PyPI publish) ---"
fi
echo

if _publish_flag "${PUBLISH_GITHUB:-0}"; then
  echo "--- publish-github ---"
  if [[ -z "${GH_TOKEN:-}" ]]; then
    echo "GH_TOKEN is required when PUBLISH_GITHUB=1" >&2
    exit 1
  fi
  docker build -f "${dockerfile}" --target ci-github-release -t ci-github-release .
  docker run --rm \
    -e GH_TOKEN="${GH_TOKEN}" \
    -e GITHUB_REPOSITORY="${GITHUB_REPOSITORY:-}" \
    -e RELEASE_TAG="${git_tag}" \
    -e CLI_VERSION="${version}" \
    -e RUNTIME_IMAGE="${runtime_image}" \
    ci-github-release
else
  echo "--- publish-github (skipped; set PUBLISH_GITHUB=1 to create release) ---"
fi

echo
echo "preview-release-workflow: ok"
