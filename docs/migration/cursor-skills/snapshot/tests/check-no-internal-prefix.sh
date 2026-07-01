#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

status=0
while IFS= read -r -d '' f; do
  case "$f" in
    */.cursor/tests/check-no-internal-prefix.sh) continue ;;
    */.cursor/tests/check-stale-skill-refs.py) continue ;;
    */.cursor/tests/README.md) continue ;;
  esac
  if rg -n 'internal-read-|internal-write-' "$f" >/dev/null 2>&1; then
    echo "ERROR: legacy internal- prefix in $f" >&2
    rg -n 'internal-read-|internal-write-' "$f" >&2 || true
    status=1
  fi
done < <(find "$REPO_ROOT/skills" "$REPO_ROOT/docs" "$REPO_ROOT/.cursor/tests" "$REPO_ROOT/README.md" -type f \( -name '*.md' -o -name '*.sh' -o -name '*.py' -o -name '*.json' \) -print0 2>/dev/null)

if [[ "$status" -ne 0 ]]; then
  exit "$status"
fi

echo "No internal-read-/internal-write- prefixes found."
