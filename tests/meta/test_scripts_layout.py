"""Shell scripts are not part of the packaged CLI runtime."""

from __future__ import annotations

from tests.constants import ROOT

SCRIPTS = ROOT / "src" / "scripts"


def test_no_shell_scripts_are_packaged() -> None:
    assert not SCRIPTS.exists()
