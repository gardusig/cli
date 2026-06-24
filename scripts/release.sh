#!/usr/bin/env bash
# Canonical PyPI release — local and GitHub Actions (cli:release container).
# See docs/release.md
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CLI_DOCKER_TARGET="${CLI_DOCKER_TARGET:-release}"
export CLI_DOCKER_IMAGE="${CLI_DOCKER_IMAGE:-cli:release}"
# shellcheck source=docker/common.sh
source "$ROOT/scripts/docker/common.sh"

resolve_release_version_host() {
  if [[ -n "${CLI_RELEASE_VERSION:-}" ]]; then
    printf '%s\n' "${CLI_RELEASE_VERSION#v}"
    return 0
  fi
  if [[ -n "${GITHUB_REF_NAME:-}" && "${GITHUB_REF_NAME}" == v* ]]; then
    printf '%s\n' "${GITHUB_REF_NAME#v}"
    return 0
  fi
  local tag
  tag="$(git -C "$ROOT" describe --tags --exact-match HEAD 2>/dev/null || true)"
  if [[ -n "$tag" ]]; then
    printf '%s\n' "${tag#v}"
    return 0
  fi
  echo "ERROR: set CLI_RELEASE_VERSION, push a v* tag, or checkout an exact version tag." >&2
  return 1
}

if [[ -z "${CLI_RELEASE_VERSION:-}" ]]; then
  export CLI_RELEASE_VERSION
  CLI_RELEASE_VERSION="$(resolve_release_version_host)"
fi

echo "==> PyPI release $CLI_RELEASE_VERSION (image: $IMAGE)"

INNER="$(docker_copy_workspace_script)
set -euo pipefail
cd '$CONTAINER_WORK'
chmod +x scripts/docker/run-release.sh scripts/pypi/*.sh
./scripts/docker/run-release.sh
"

docker_run_release "$INNER"
