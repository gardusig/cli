#!/usr/bin/env bash
# Host-only helper: print the version on origin/main. Do not run inside Docker.
set -euo pipefail

ref="${1:-origin/main}"
git fetch origin main 2>/dev/null || true
python3 - <<'PY' "$ref"
import subprocess
import sys
import tomllib

ref = sys.argv[1]
text = subprocess.check_output(["git", "show", f"{ref}:pyproject.toml"], text=True)
print(tomllib.loads(text.encode())["project"]["version"])
PY
