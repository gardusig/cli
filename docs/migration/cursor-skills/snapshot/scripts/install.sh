#!/usr/bin/env bash
# Install Cursor skills from this repository into ~/.cursor/skills.
# Default behavior: copy repo skills to destination and verify byte match.
# Optional --clean: clear destination skills directory (only) before copy.
#
# Path flattening examples:
# - skills/git/review/SKILL.md -> ~/.cursor/skills/git-review/SKILL.md
# - skills/internal/read/dependencies/discover/SKILL.md -> ~/.cursor/skills/read-dependencies-discover/SKILL.md
# - skills/gh/issue/view/SKILL.md -> ~/.cursor/skills/gh-issue-view/SKILL.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEST="${CURSOR_SKILLS_DIR:-$HOME/.cursor/skills}"

CLEAN=0
DRY_RUN=0
VERIFY_ONLY=0

usage() {
  cat <<'EOF'
Usage: .cursor/scripts/install.sh [options]

Default:
  Copy all repo skills from skills/** to $CURSOR_SKILLS_DIR (or ~/.cursor/skills),
  then verify each installed SKILL.md is byte-identical to the repo source.

Options:
  --clean        Confirm, clear $CURSOR_SKILLS_DIR, then copy + verify
  --dry-run      Print planned actions only (no writes, no cmp)
  --verify-only  Verify installed skills match repo (cmp), no copy
  --repo DIR     Repository root containing skills/ (default: parent of .cursor/scripts/)
  -h, --help     Show this help

Environment:
  CURSOR_SKILLS_DIR            Destination directory (default: ~/.cursor/skills)
  CURSOR_SKILLS_CLEAN_CONFIRM  Set to "yes" to auto-confirm --clean
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --clean) CLEAN=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --verify-only) VERIFY_ONLY=1; shift ;;
    --repo)
      REPO_ROOT="$(cd "$2" && pwd)"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

SKILLS_DIR="$REPO_ROOT/skills"
if [[ ! -d "$SKILLS_DIR" ]]; then
  echo "ERROR: missing skills directory: $SKILLS_DIR" >&2
  exit 1
fi

flatten_skill_name() {
  local name="$1"
  case "$name" in
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

  if [[ "$repo_file" != skills/* ]]; then
    echo "ERROR: unsupported skill path: $repo_file" >&2
    return 1
  fi

  rel="${repo_file#skills/}"
  if [[ "$rel" == "SKILL.md" ]]; then
    name=""
  else
    name="${rel%/SKILL.md}"
  fi
  flatten_skill_name "$name"
}

enumerate_install_skills() {
  (
    cd "$REPO_ROOT"
    find skills -name SKILL.md -print0
  ) | sort -z
}

count_install_skills() {
  local n=0
  while IFS= read -r -d '' _; do
    n=$((n + 1))
  done < <(enumerate_install_skills)
  echo "$n"
}

verify_skills_installed() {
  local mismatches=0
  local walked=0
  local flat dest_file src

  while IFS= read -r -d '' f; do
    walked=$((walked + 1))
    flat="$(to_flat_name "$f")"
    dest_file="$DEST/$flat/SKILL.md"
    src="$REPO_ROOT/$f"
    if [[ ! -f "$dest_file" ]]; then
      echo "ERROR: missing destination: $dest_file (expected from $src)" >&2
      mismatches=$((mismatches + 1))
    elif ! cmp -s "$src" "$dest_file"; then
      echo "ERROR: content differs: $src vs $dest_file" >&2
      mismatches=$((mismatches + 1))
    fi
  done < <(enumerate_install_skills)

  local expected
  expected="$(count_install_skills)"
  if [[ "$walked" -ne "$expected" ]]; then
    echo "ERROR: internal count mismatch (walked $walked, expected $expected)" >&2
    return 1
  fi
  if [[ "$mismatches" -gt 0 ]]; then
    echo "ERROR: verify failed ($mismatches issue(s)) for $walked skill(s)" >&2
    return 1
  fi
  echo "Verified $walked skill(s) in $DEST"
}

clean_destination() {
  if [[ "$DEST" == "/" || -z "$DEST" ]]; then
    echo "ERROR: refusing to clean unsafe DEST: '$DEST'" >&2
    return 1
  fi

  echo "WARNING: --clean will remove ALL files/directories inside:"
  echo "  $DEST"
  echo "Scope is destination skills directory only."

  local confirmed=0
  if [[ "${CURSOR_SKILLS_CLEAN_CONFIRM:-}" == "yes" ]]; then
    confirmed=1
  elif [[ -t 0 ]]; then
    read -r -p "Type DELETE to continue: " response
    if [[ "$response" == "DELETE" ]]; then
      confirmed=1
    fi
  else
    echo "ERROR: --clean requires TTY confirmation or CURSOR_SKILLS_CLEAN_CONFIRM=yes" >&2
    return 1
  fi

  if [[ "$confirmed" -ne 1 ]]; then
    echo "Aborted clean."
    return 1
  fi

  shopt -s dotglob nullglob
  local entries=("$DEST"/*)
  if [[ "${#entries[@]}" -gt 0 ]]; then
    rm -rf "${entries[@]}"
  fi
  shopt -u dotglob nullglob
  echo "Cleaned destination: $DEST"
}

copy_skills() {
  local flat target src
  while IFS= read -r -d '' f; do
    flat="$(to_flat_name "$f")"
    target="$DEST/$flat"
    src="$REPO_ROOT/$f"
    mkdir -p "$target"
    cp -f "$src" "$target/SKILL.md"
  done < <(enumerate_install_skills)
}

N="$(count_install_skills)"
if [[ "$N" -eq 0 ]]; then
  echo "ERROR: no SKILL.md found under $REPO_ROOT/skills" >&2
  exit 1
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  if [[ "$VERIFY_ONLY" -eq 1 ]]; then
    echo "Dry run: would verify $N skill(s) under $DEST"
    while IFS= read -r -d '' f; do
      flat="$(to_flat_name "$f")"
      printf 'would check: %s -> %s/SKILL.md\n' "$REPO_ROOT/$f" "$DEST/$flat"
    done < <(enumerate_install_skills)
  else
    if [[ "$CLEAN" -eq 1 ]]; then
      echo "Dry run: would clear destination directory first: $DEST"
    fi
    while IFS= read -r -d '' f; do
      flat="$(to_flat_name "$f")"
      printf 'would copy: %s -> %s/%s/SKILL.md\n' "$REPO_ROOT/$f" "$DEST" "$flat"
    done < <(enumerate_install_skills)
    echo "Dry run: would verify copied files match repo sources"
  fi
  exit 0
fi

mkdir -p "$DEST"

if [[ "$VERIFY_ONLY" -eq 1 ]]; then
  verify_skills_installed
  exit 0
fi

if [[ "$CLEAN" -eq 1 ]]; then
  clean_destination
fi

copy_skills
echo "Installed $N skill(s) into $DEST"
verify_skills_installed
echo "Restart Cursor once if @ or / does not list the skills yet."
