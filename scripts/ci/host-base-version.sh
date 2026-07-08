#!/usr/bin/env bash
# Host-only helper: print the version on origin/main. Do not run inside Docker.
set -euo pipefail

ref="${1:-origin/main}"
git fetch origin main 2>/dev/null || true
python3 - <<'PY' "$ref"
import io
import subprocess
import sys
import tomllib

ref = sys.argv[1]
raw = subprocess.check_output(["git", "show", f"{ref}:pyproject.toml"])
print(tomllib.load(io.BytesIO(raw))["project"]["version"])
PY
