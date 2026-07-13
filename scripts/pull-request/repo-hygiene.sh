#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

root="$(gh_repo_root)"
cd "$root"
stage_ensure_dev

if [[ -n "${HYGIENE_POLICY_JSON:-}" ]]; then
  export HYGIENE_POLICY_JSON
  python3 tests/meta/hygiene_gate.py
else
  python3 tests/meta/hygiene_gate.py
fi
