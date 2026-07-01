#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_DIR="$SCRIPT_DIR"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MANIFEST_FILE="$TESTS_DIR/write-guard-manifest.txt"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

has_guard_keywords() {
  local file="$1"
  grep -Eqi '(AskQuestion|Proceed|confirm|Goal|structured confirm|read-safety-structured-qa|read-safety-skill-safety|structured-qa|skill-safety)' "$file"
}

check_file() {
  local file="$1"
  [[ -f "$file" ]] || fail "missing file: $file"
  has_guard_keywords "$file" || fail "$file missing write-safety keywords"
}

check_write_libraries() {
  while IFS= read -r -d '' file; do
    case "$file" in
      "$REPO_ROOT/skills/internal/write/"*/SKILL.md)
        # Domain hubs in skills/write/* can remain high-level.
        continue
        ;;
    esac
    check_file "$file"
  done < <(find "$REPO_ROOT/skills/internal/write" -name SKILL.md -print0 | sort -z)
}

check_manifest_skills() {
  [[ -f "$MANIFEST_FILE" ]] || fail "missing manifest file: $MANIFEST_FILE"
  while IFS= read -r rel; do
    [[ -z "$rel" || "${rel#\#}" != "$rel" ]] && continue
    check_file "$REPO_ROOT/$rel"
  done < "$MANIFEST_FILE"
}

# read/ libraries are intentionally out of scope for this write guard.
check_write_libraries
check_manifest_skills

echo "Write skill keyword checks passed."
