#!/usr/bin/env bash
# Dev install: editable gardusig-cli from this repo clone into ~/.local/bin/cli.
# End users: ./scripts/install-pypi.sh (latest from PyPI, no clone required).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_install_common.sh
source "$SCRIPT_DIR/_install_common.sh"

DEST="$CLI_INSTALL_DEST"
VENV="$ROOT/.venv"
PYTHON="$VENV/bin/python"

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

remove_stale_binaries "$DEST"
ensure_cli_path_in_all_profiles
verify_cli_binary "$DEST/cli"

echo ""
echo "Installed: $DEST/cli (editable dev build from $ROOT)"
echo "Version:   $("$DEST/cli" --version)"
echo ""
echo "For PyPI releases instead: ./scripts/install-pypi.sh"
install_cli_path_hint
