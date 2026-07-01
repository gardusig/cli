#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

flatten_skill_name() {
  local name="$1"
  case "$name" in
    internal/read/*)
      local sub="${name#internal/read/}"
      printf 'read-%s' "${sub//\//-}"
      ;;
    internal/write/*)
      local sub="${name#internal/write/}"
      printf 'write-%s' "${sub//\//-}"
      ;;
    read/*)
      local sub="${name#read/}"
      printf 'read-%s' "${sub//\//-}"
      ;;
    write/*)
      local sub="${name#write/}"
      printf 'write-%s' "${sub//\//-}"
      ;;
    gh/issue)
      printf 'gh-issue'
      ;;
    gh/issue/*)
      local sub="${name#gh/issue/}"
      printf 'gh-issue-%s' "${sub//\//-}"
      ;;
    *) printf '%s' "${name//\//-}" ;;
  esac
}

to_flat_name() {
  local repo_file="$1"
  local rel name

  if [[ "$repo_file" == skills/* ]]; then
    rel="${repo_file#skills/}"
    if [[ "$rel" == "SKILL.md" ]]; then
      name=""
    else
      name="${rel%/SKILL.md}"
    fi
    flatten_skill_name "$name"
  else
    echo "ERROR: unsupported skill path: $repo_file" >&2
    return 1
  fi
}

status=0
while IFS= read -r -d '' abs_file; do
  rel_file="${abs_file#$REPO_ROOT/}"
  expected="$(to_flat_name "$rel_file")"
  actual="$(awk '/^name:[[:space:]]*/ {print $2; exit}' "$abs_file")"
  if [[ -z "$actual" ]]; then
    echo "ERROR: missing name in $rel_file" >&2
    status=1
    continue
  fi
  if [[ "$actual" != "$expected" ]]; then
    echo "ERROR: name mismatch in $rel_file (actual: $actual, expected: $expected)" >&2
    status=1
  fi
done < <(find "$REPO_ROOT/skills" -name SKILL.md -print0 | sort -z)

if [[ "$status" -ne 0 ]]; then
  exit "$status"
fi

echo "Skill name checks passed."
