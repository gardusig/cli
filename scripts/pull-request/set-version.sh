#!/usr/bin/env bash
# Set pyproject.toml + src/__init__.py to the next PyPI-compatible version.
# Patch-bumps the greatest published PyPI/TestPyPI release; on first publish keeps a valid
# working-tree version or falls back to 0.1.0.
set -euo pipefail
# shellcheck source=scripts/_common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../_common.sh"

root="$(gh_repo_root)"
cd "$root"

dry_run=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) dry_run=1 ;;
    -h | --help)
      cat <<'EOF'
Usage: scripts/pull-request/set-version.sh [--dry-run]

Writes the next semver to pyproject.toml and src/__init__.py:
  - when PyPI or TestPyPI has releases: patch-bump the greatest published version
  - when none yet: keep a valid pyproject version, else 0.1.0

Prints the chosen version on stdout.
EOF
      exit 0
      ;;
    *)
      echo "unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

published="$(bash "$(dirname "${BASH_SOURCE[0]}")/host-last-published-version.sh" || true)"
version="$(python3 - <<'PY' "$root" "$published"
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
published = sys.argv[2].strip()
default = "0.1.0"

def parse(version: str) -> tuple[int, int, int]:
    core = version.strip().lstrip("v")
    parts = core.split(".")
    if len(parts) < 3:
        raise ValueError(version)
    nums: list[int] = []
    for piece in parts[:3]:
        digits = ""
        for char in piece:
            if char.isdigit():
                digits += char
            else:
                break
        nums.append(int(digits or "0"))
    return nums[0], nums[1], nums[2]

def bump_patch(version: str) -> str:
    major, minor, patch = parse(version)
    return f"{major}.{minor}.{patch + 1}"

def read_project_version() -> str:
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'version\s*=\s*"([^"]+)"', text)
    if not match:
        raise ValueError("version not found in pyproject.toml")
    return match.group(1)

if published:
    print(bump_patch(published))
else:
    try:
        major, minor, patch = parse(read_project_version())
        print(f"{major}.{minor}.{patch}")
    except ValueError:
        print(default)
PY
)"

if [[ "$dry_run" -eq 1 ]]; then
  echo "$version"
  exit 0
fi

python3 - <<'PY' "$root" "$version"
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
version = sys.argv[2]
pyproject = root / "pyproject.toml"
init_py = root / "src" / "__init__.py"

text = pyproject.read_text(encoding="utf-8")
new_text, count = re.subn(
    r'^(version\s*=\s*")[^"]+(")',
    rf'\g<1>{version}\g<2>',
    text,
    count=1,
    flags=re.MULTILINE,
)
if count != 1:
    raise SystemExit("failed to update version in pyproject.toml")
pyproject.write_text(new_text, encoding="utf-8")

init_text = init_py.read_text(encoding="utf-8")
new_init, init_count = re.subn(
    r'^__version__\s*=\s*"[^"]+"',
    f'__version__ = "{version}"',
    init_text,
    count=1,
    flags=re.MULTILINE,
)
if init_count != 1:
    raise SystemExit("failed to update __version__ in src/__init__.py")
init_py.write_text(new_init, encoding="utf-8")
PY

echo "$version"
