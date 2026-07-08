#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/ci/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

root="$(ci_repo_root)"
cd "$root"

base_ref="${BASE_REF:-origin/main}"
if [[ -n "${BASE_VERSION:-}" ]]; then
  base_version="$BASE_VERSION"
elif git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git fetch origin main 2>/dev/null || true
  base_version="$(python3 - <<'PY' "$base_ref"
import subprocess
import sys
import tomllib

ref = sys.argv[1]
text = subprocess.check_output(
    ["git", "show", f"{ref}:pyproject.toml"],
    text=True,
)
print(tomllib.loads(text.encode())["project"]["version"])
PY
)"
else
  echo "version-check: set BASE_VERSION when .git is not in the build context (Docker COPY excludes .git)" >&2
  exit 1
fi

head_version="$(ci_read_project_version "$root")"
ci_compare_versions "$base_version" "$head_version"
