#!/usr/bin/env bash
# In-container: version from tag / GITHUB_REF_NAME → build + PyPI upload.
set -euo pipefail
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"

resolve_release_version() {
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
  echo "ERROR: set CLI_RELEASE_VERSION or run from an annotated version tag (v*)" >&2
  return 1
}

export CLI_RELEASE_VERSION
CLI_RELEASE_VERSION="$(resolve_release_version)"
echo "==> release version: $CLI_RELEASE_VERSION"
exec "$PYPI_DIR/upload.sh" "$@"
