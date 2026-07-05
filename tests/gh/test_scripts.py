from tests.constants import ROOT

"""Verify src/scripts/gh wrappers exist."""

from pathlib import Path

from src.utils.catalog import GH_SCRIPT_COMMANDS


GH_SCRIPTS = ROOT / "src" / "scripts" / "gh"


def test_all_gh_script_wrappers_exist() -> None:
    expected = {name for name, _ in GH_SCRIPT_COMMANDS}
    found = {p.name for p in GH_SCRIPTS.glob("*.sh") if p.name != "_common.sh"}
    assert expected <= found
