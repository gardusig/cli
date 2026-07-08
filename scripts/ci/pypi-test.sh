#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/ci/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

ci_ensure_dev
root="$(ci_repo_root)"
version="${CLI_RELEASE_VERSION:-$(ci_read_project_version "$root")}"

rm -rf dist
python -m build --outdir dist
versioned="$(ci_read_project_version "$root")"
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
