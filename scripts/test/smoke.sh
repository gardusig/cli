#!/usr/bin/env bash
# Integration smoke (container only — invoked by scripts/docker/run-integration.sh).
set -euo pipefail
if [[ "${CLI_DOCKER_INTEGRATION:-}" != "1" ]]; then
  echo "ERROR: scripts/test/smoke.sh must run inside the Docker integration image." >&2
  exit 1
fi

ROOT="${CLI_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$ROOT"
export CLI_CONFIG_DIR="${CLI_CONFIG_DIR:-$ROOT/config/ci}"
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

python -m src --help >/dev/null
smoke_contains "0.1.0" python -m src --version

smoke_contains "Repository:" python -m src drive status
smoke_contains "restore: not implemented yet" python -m src restore
smoke_contains "upload" python -m src drive --help
smoke_contains "ingest" python -m src notion --help
smoke_contains "bookmarks" python -m src chrome --help
smoke_contains "deploy" python -m src notion --help

links_out="$(mktemp)"
python -m src links >"$links_out" 2>&1
grep -q "Quick defaults" "$links_out"
rm -f "$links_out"

bash -n scripts/docker/bootstrap.sh scripts/pypi/install.sh scripts/pypi/_common.sh scripts/notion/_common.sh
bash -n scripts/chrome/*.sh
bash -n scripts/git/*.sh

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

downloads="$tmpdir/Downloads"
bookmarks_dir="$tmpdir/data/bookmarks"
mkdir -p "$downloads" "$bookmarks_dir"

cp tests/fixtures/bookmarks.html "$downloads/bookmarks.html"

CLI_ROOT="$tmpdir" \
CLI_DOWNLOADS_DIR="$downloads" \
CLI_BOOKMARKS_FILE="$bookmarks_dir/bookmarks.html" \
CLI_SKIP_CHROME_AUTOMATION=1 \
scripts/chrome/export.sh

test -s "$bookmarks_dir/bookmarks.html"
grep -q "Cli Test Bookmark" "$bookmarks_dir/bookmarks.html"

CLI_ROOT="$tmpdir" \
CLI_BOOKMARKS_FILE="$bookmarks_dir/bookmarks.html" \
CLI_SKIP_CHROME_AUTOMATION=1 \
scripts/chrome/import.sh | grep -q "Import complete"

git init -b main "$tmpdir/repo" >/dev/null
git -C "$tmpdir/repo" config user.email "cli@example.test"
git -C "$tmpdir/repo" config user.name "Cli Test"
touch "$tmpdir/repo/README.md"
git -C "$tmpdir/repo" add README.md
git -C "$tmpdir/repo" commit -m "initial" >/dev/null

(
  cd "$tmpdir/repo"
  smoke_contains "smoke-branch" python -m src git start smoke-branch --no-prep
  test "$(git branch --show-current)" = "smoke-branch"
)

python tests/integration/check_integration_coverage.py
python tests/integration/check_public_commands.py
python tests/integration/check_workflow_integration.py
python tests/integration/check_api_integration.py

echo "Docker integration smoke passed."
