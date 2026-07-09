#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/ci/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

root="$(ci_repo_root)"
current="$(ci_read_project_version "$root")"
python3 - <<'PY' "$current"
import sys

parts = [int(p) for p in sys.argv[1].split(".")]
parts[-1] += 1
print(".".join(str(p) for p in parts))
PY
