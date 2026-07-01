#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_DIR="$SCRIPT_DIR"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REGISTRY_FILE="$TESTS_DIR/public-skills.txt"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

contains_name_and_description() {
  local file="$1"
  grep -Eq '^name:[[:space:]]*\S+' "$file" || return 1
  grep -Eq '^description:[[:space:]]*\S+' "$file" || return 1
}

skill_name() {
  local file="$1"
  awk '/^name:[[:space:]]*/ {print $2; exit}' "$file"
}

check_unique_skill_names() {
  local names_tmp duplicates_tmp name
  names_tmp="$(mktemp)"
  duplicates_tmp="$(mktemp)"

  while IFS= read -r -d '' skill; do
    name="$(skill_name "$skill")"
    [[ -n "$name" ]] || fail "$skill missing name field"
    printf '%s\t%s\n' "$name" "${skill#$REPO_ROOT/}" >> "$names_tmp"
  done < <(find "$REPO_ROOT/skills" -name SKILL.md -print0 | sort -z)

  cut -f1 "$names_tmp" | LC_ALL=C sort | uniq -d > "$duplicates_tmp"
  if [[ -s "$duplicates_tmp" ]]; then
    while IFS= read -r dup_name; do
      echo "Duplicate skill name: $dup_name" >&2
      awk -F'\t' -v n="$dup_name" '$1 == n {print "  - " $2}' "$names_tmp" >&2
    done < "$duplicates_tmp"
    fail "duplicate skill names detected across skills/**/SKILL.md"
  fi

  rm -f "$names_tmp" "$duplicates_tmp"
}

check_write_git_pairing() {
  local public_abs="$1"
  local rel segment write_abs actual expected write_rel

  [[ "$public_abs" == "$REPO_ROOT/skills/git/"* ]] || return 0

  rel="${public_abs#$REPO_ROOT/skills/git/}"
  segment="${rel%/SKILL.md}"
  [[ "$segment" == "$rel" ]] && return 0

  write_abs="$REPO_ROOT/skills/internal/write/$segment/SKILL.md"
  [[ -f "$write_abs" ]] || return 0

  actual="$(skill_name "$write_abs")"
  write_rel="${write_abs#$REPO_ROOT/skills/internal/write/}"
  write_rel="${write_rel%/SKILL.md}"
  expected="write-${write_rel//\//-}"
  [[ "$actual" == "$expected" ]] || fail "$write_abs name mismatch (actual: $actual, expected: $expected)"
}

is_mutating_public_skill() {
  local file="$1"
  case "$file" in
    */skills/git/branch/SKILL.md|\
    */skills/git/main/SKILL.md|\
    */skills/git/pull/SKILL.md|\
    */skills/git/push/SKILL.md|\
    */skills/git/rebase/SKILL.md|\
    */skills/git/reset/SKILL.md|\
    */skills/git/revert/SKILL.md|\
    */skills/git/cherry/pick/SKILL.md|\
    */skills/git/start/SKILL.md|\
    */skills/git/stash/SKILL.md|\
    */skills/git/commit/SKILL.md|\
    */skills/gh/issue/execute/SKILL.md|\
    */skills/git/tag/SKILL.md|\
    */skills/git/post/merge/cleanup/SKILL.md|\
    */skills/gh/issue/SKILL.md|\
    */skills/gh/issue/close/SKILL.md|\
    */skills/gh/issue/delete/closed/SKILL.md|\
    */skills/gh/pr/SKILL.md|\
    */skills/gh/pr/close/SKILL.md)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

public_skill_files() {
  (
    cd "$REPO_ROOT"
    find skills -name SKILL.md -print0
  ) | while IFS= read -r -d '' f; do
    case "$f" in
      skills/git/*/SKILL.md|skills/git/*/*/SKILL.md|skills/git/*/*/*/SKILL.md|skills/git/*/*/*/*/SKILL.md|\
      skills/gh/*/SKILL.md|skills/gh/*/*/SKILL.md|skills/gh/*/*/*/SKILL.md|skills/gh/*/*/*/*/SKILL.md)
        ;;
      *)
        continue
        ;;
    esac
    printf '%s\0' "$f"
  done
}

[[ -f "$REGISTRY_FILE" ]] || fail "missing registry file: $REGISTRY_FILE"

actual_tmp="$(mktemp)"
expected_tmp="$(mktemp)"
trap 'rm -f "$actual_tmp" "$expected_tmp"' EXIT

check_unique_skill_names

while IFS= read -r -d '' file; do
  abs="$REPO_ROOT/$file"
  contains_name_and_description "$abs" || fail "$abs missing non-empty name or description"
  check_write_git_pairing "$abs"

  if is_mutating_public_skill "$abs"; then
    grep -Eqi '(write gate|read-safety-structured-qa|Proceed|confirm|Goal)' "$abs" \
      || fail "$abs missing mutation guard keywords (write gate|read-safety-structured-qa|Proceed|confirm|Goal)"
  fi
  printf '%s\n' "$file" >> "$actual_tmp"
done < <(public_skill_files)

LC_ALL=C sort -o "$actual_tmp" "$actual_tmp"
LC_ALL=C sort "$REGISTRY_FILE" > "$expected_tmp"

if ! diff -u "$expected_tmp" "$actual_tmp" >/dev/null; then
  echo "Registry mismatch in .cursor/tests/public-skills.txt" >&2
  diff -u "$expected_tmp" "$actual_tmp" >&2 || true
  exit 1
fi

echo "Public skill checks passed (including registry)."
