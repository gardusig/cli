#!/usr/bin/env bash
# Print the full-suite contract (nightly / ci:full safety net).
set -euo pipefail
# shellcheck source=scripts/test/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

root="$(repo_root)"
export CLI_CONFIG_DIR="${CLI_CONFIG_DIR:-config/ci}"
cd "$root"

format="${FORMAT:-table}"
if [[ "$format" == "json" ]]; then
  python3 - <<'PY'
import json

packages = ["gh", "git", "notion", "drive", "chrome", "docker", "contest", "project", "pypi"]
print(json.dumps({"packages": packages, "contract": "scripts/test/all.sh"}, indent=2))
PY
  exit 0
fi

echo "Full suite: scripts/ci/unit-test.sh + scripts/ci/integration-test.sh"
echo "Packages with scripts/test wrappers: gh git notion drive chrome docker contest project pypi"
