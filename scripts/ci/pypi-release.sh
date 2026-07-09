#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/ci/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

ci_ensure_dev
root="$(ci_repo_root)"
version="${CLI_RELEASE_VERSION:?CLI_RELEASE_VERSION is required}"

if [[ -z "${PYPI_API_TOKEN:-}" ]]; then
  echo "PYPI_API_TOKEN is required" >&2
  exit 1
fi

tag_version="${version#v}"
project_version="$(ci_read_project_version "$root")"
if [[ "$tag_version" != "$project_version" ]]; then
  echo "tag/version mismatch: CLI_RELEASE_VERSION=$tag_version pyproject=$project_version" >&2
  exit 1
fi

rm -rf dist
pip install --no-cache-dir 'setuptools>=61,<77' build twine
python -m build --outdir dist
export TWINE_USERNAME=__token__
export TWINE_PASSWORD="$PYPI_API_TOKEN"
twine upload dist/* --skip-existing
