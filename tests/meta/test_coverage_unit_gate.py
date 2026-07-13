"""Guardrails: unit test job must enforce ≥80% coverage (Docker / CI gate)."""

from __future__ import annotations

from tests.constants import ROOT

import configparser
from pathlib import Path


UNIT_COV_CONFIG = ROOT / "coverage-unit.ini"


def test_coverage_unit_ini_requires_eighty_percent() -> None:
    cfg = configparser.ConfigParser()
    cfg.read(UNIT_COV_CONFIG)
    assert int(cfg["report"]["fail_under"]) == 80
    omit = cfg["run"].get("omit", "")
    assert "src/integration" in omit
    assert "src/commands/chat.py" in omit
    for hidden in (
        "src/commands/backup.py",
        "src/commands/bookmarks.py",
        "src/commands/hygiene.py",
        "src/commands/publish.py",
    ):
        assert hidden in omit


def test_coverage_unit_ini_scopes_cli_package() -> None:
    cfg = configparser.ConfigParser()
    cfg.read(UNIT_COV_CONFIG)
    source = cfg["run"]["source"].strip()
    assert source == "src"
    include = cfg["report"].get("include", "")
    assert "src/cli.py" in include
    assert "src/commands" in include


