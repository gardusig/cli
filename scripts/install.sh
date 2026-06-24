#!/usr/bin/env bash
# Install cli globally into ~/.local/bin (macOS-friendly; works in any terminal).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${CLI_INSTALL_DIR:-$HOME/.local/bin}"
VENV="$ROOT/.venv"
PYTHON="$VENV/bin/python"
PATH_MARKER='# cli (gardusig/cli)'
PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'

if [[ ! -d "$VENV" ]]; then
  echo "Running bootstrap first..."
  "$ROOT/scripts/bootstrap.sh"
fi

mkdir -p "$DEST"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
pip install -e "$ROOT" -q

cat >"$DEST/cli" <<EOF
#!/usr/bin/env bash
exec "$PYTHON" -m gardusig_cli "\$@"
EOF
chmod +x "$DEST/cli"

# Remove stale binary from prior install (no alias kept).
[[ -f "$DEST/shuttle" ]] && rm -f "$DEST/shuttle"

ensure_path_in_profile() {
  local profile="$1"
  [[ -f "$profile" ]] || return 0
  if grep -qF '.local/bin' "$profile" 2>/dev/null; then
    return 0
  fi
  {
    echo ""
    echo "$PATH_MARKER"
    echo "$PATH_LINE"
  } >>"$profile"
  echo "Added ~/.local/bin to PATH in $profile"
}

ensure_path_in_profile "$HOME/.zprofile"
ensure_path_in_profile "$HOME/.zshrc"
ensure_path_in_profile "$HOME/.bash_profile"

if ! "$DEST/cli" --version >/dev/null 2>&1; then
  echo "ERROR: install verification failed — $DEST/cli --version" >&2
  exit 1
fi

echo ""
echo "Installed: $DEST/cli"
echo "Version:   $("$DEST/cli" --version)"
echo ""
echo "Open a new terminal (or run: source ~/.zprofile) then try: cli --help"
