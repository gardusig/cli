#!/usr/bin/env bash
# Integration smoke (container only — invoked by scripts/docker/run-integration.sh).
set -euo pipefail

ROOT="${SHUTTLE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$ROOT"
export SHUTTLE_CONFIG_DIR="${SHUTTLE_CONFIG_DIR:-$ROOT/config/ci}"
export PYTHONUNBUFFERED=1

# grep -q in a pipefail pipeline can yield SIGPIPE from the writer; capture output instead.
smoke_contains() {
  local needle="$1"
  shift
  local output
  output=$("$@" 2>&1)
  if ! grep -qF "$needle" <<<"$output"; then
    echo "smoke: expected to find ${needle} in output of: $*" >&2
    echo "$output" >&2
    return 1
  fi
}

python -m shuttle --help >/dev/null
smoke_contains "0.1.0" python -m shuttle --version

smoke_contains "Repository:" python -m shuttle drive status
smoke_contains "restore: not implemented yet" python -m shuttle restore
smoke_contains "upload" python -m shuttle drive --help
smoke_contains "ingest" python -m shuttle notion --help
smoke_contains "bookmarks" python -m shuttle chrome --help
smoke_contains "deploy" python -m shuttle notion --help

links_out="$(mktemp)"
python -m shuttle links >"$links_out" 2>&1
grep -q "Quick defaults" "$links_out"
rm -f "$links_out"

bash -n scripts/bootstrap.sh scripts/install.sh
bash -n scripts/chrome/*.sh
bash -n scripts/git/*.sh

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

downloads="$tmpdir/Downloads"
bookmarks_dir="$tmpdir/data/bookmarks"
mkdir -p "$downloads" "$bookmarks_dir"

cp tests/fixtures/bookmarks.html "$downloads/bookmarks.html"

SHUTTLE_ROOT="$tmpdir" \
SHUTTLE_DOWNLOADS_DIR="$downloads" \
SHUTTLE_BOOKMARKS_FILE="$bookmarks_dir/bookmarks.html" \
SHUTTLE_SKIP_CHROME_AUTOMATION=1 \
scripts/chrome/export-bookmarks.sh

test -s "$bookmarks_dir/bookmarks.html"
grep -q "Shuttle Test Bookmark" "$bookmarks_dir/bookmarks.html"

SHUTTLE_ROOT="$tmpdir" \
SHUTTLE_BOOKMARKS_FILE="$bookmarks_dir/bookmarks.html" \
SHUTTLE_SKIP_CHROME_AUTOMATION=1 \
scripts/chrome/import-bookmarks.sh | grep -q "Import complete"

git init -b main "$tmpdir/repo" >/dev/null
git -C "$tmpdir/repo" config user.email "shuttle@example.test"
git -C "$tmpdir/repo" config user.name "Shuttle Test"
touch "$tmpdir/repo/README.md"
git -C "$tmpdir/repo" add README.md
git -C "$tmpdir/repo" commit -m "initial" >/dev/null

(
  cd "$tmpdir/repo"
  smoke_contains "smoke-branch" python -m shuttle git start smoke-branch --no-prep
  test "$(git branch --show-current)" = "smoke-branch"
)

python tests/integration/check_integration_coverage.py
python tests/integration/check_public_commands.py
python tests/integration/check_workflow_integration.py
python tests/integration/check_api_integration.py

echo "Docker integration smoke passed."
