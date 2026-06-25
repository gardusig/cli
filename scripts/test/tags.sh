#!/usr/bin/env bash
# Fast host pytest for git tag / zip / version policy (debug without Docker).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
# shellcheck source=../_common.sh
source "$ROOT/scripts/_common.sh"
load_repo_env

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="python3"
else
  echo "ERROR: no python; run ./scripts/pypi/install.sh" >&2
  exit 1
fi

export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export CLI_CONFIG_DIR="${CLI_CONFIG_DIR:-$ROOT/config/ci}"

echo "==> tag / zip / version unit tests"
"$PY" -m pytest \
  tests/git/test_tag_policy.py \
  tests/git/test_tag_zip.py \
  tests/git/test_commands.py::test_git_zip_defaults_to_latest_local_tag \
  tests/git/test_commands.py::test_git_zip_explicit_tag \
  tests/git/test_commands.py::test_git_tag_default_name \
  tests/pypi/test_commands.py::test_pypi_version_check_ok \
  tests/pypi/test_commands.py::test_pypi_version_check_fails \
  -q "$@"
