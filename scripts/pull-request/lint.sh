#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

root="$(gh_repo_root)"
cd "$root"

if ! command -v markdownlint-cli2 >/dev/null 2>&1; then
  echo "markdownlint-cli2 is required" >&2
  exit 1
fi

mapfile -t md_files < <(find . -type f -name '*.md' \
  ! -path './.git/*' \
  ! -path './.venv/*' \
  ! -path './dist/*' \
  | sort)

if ((${#md_files[@]} == 0)); then
  echo "no markdown files found"
  exit 0
fi

markdownlint-cli2 "${md_files[@]}"

if [[ "${CLI_LINT_MERMAID:-1}" != "0" ]] && command -v mmdc >/dev/null 2>&1; then
  python3 tests/meta/lint_mermaid_gate.py
fi

echo "lint ok"
