#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

stage_ensure_dev
root="$(gh_repo_root)"
version="$(gh_strip_v_prefix "${CLI_RELEASE_VERSION:?CLI_RELEASE_VERSION is required}")"
gh_set_project_version "$root" "$version"

_publish_pypi() {
  if [[ -z "${PYPI_API_TOKEN:-}" ]]; then
    echo "PYPI_API_TOKEN is required" >&2
    exit 1
  fi

  rm -rf dist
  pip install --no-cache-dir 'setuptools>=61,<77' build twine
  python -m build --outdir dist
  export TWINE_USERNAME=__token__
  export TWINE_PASSWORD="$PYPI_API_TOKEN"
  twine upload dist/* --skip-existing
}

stage_run_with_timeout "${CI_TESTPYPI_TIMEOUT}" _publish_pypi
