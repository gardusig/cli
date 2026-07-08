#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/ci/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

root="$(ci_repo_root)"
cd "$root"

base_ref="${BASE_REF:-origin/main}"
if [[ -n "${BASE_VERSION:-}" ]]; then
  base_version="$BASE_VERSION"
else
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
fi

head_version="$(ci_read_project_version "$root")"
ci_compare_versions "$base_version" "$head_version"
