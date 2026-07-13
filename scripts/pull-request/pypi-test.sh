#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

stage_ensure_dev
root="$(gh_repo_root)"
version="${CLI_RELEASE_VERSION:-$(gh_read_project_version "$root")}"

rm -rf dist
pip install --no-cache-dir 'setuptools>=61,<77' build twine
python -m build --outdir dist
versioned="$(gh_read_project_version "$root")"
if [[ "$version" != "$versioned" ]]; then
  echo "CLI_RELEASE_VERSION=$version does not match pyproject.toml=$versioned" >&2
  exit 1
fi

if [[ -z "${TESTPYPI_API_TOKEN:-}" ]]; then
  echo "skip TestPyPI upload (TESTPYPI_API_TOKEN not set)"
  exit 0
fi

export TWINE_USERNAME=__token__
export TWINE_PASSWORD="$TESTPYPI_API_TOKEN"
twine upload --repository-url https://test.pypi.org/legacy/ dist/* --skip-existing
