#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=scripts/ci/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

root="$(ci_repo_root)"
cd "$root"
ci_ensure_dev

if [[ -n "${HYGIENE_POLICY_JSON:-}" ]]; then
  export HYGIENE_POLICY_JSON
  python3 tests/meta/hygiene_gate.py
else
  python3 tests/meta/hygiene_gate.py
fi
