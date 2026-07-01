"""Guardrails: unit test job must enforce ≥80% coverage (Docker / CI gate)."""

from __future__ import annotations

from tests.constants import ROOT

import configparser
from pathlib import Path


UNIT_COV_CONFIG = ROOT / "coverage-unit.ini"
RUN_UNIT = ROOT / "scripts/docker/run-unit.sh"


def test_coverage_unit_ini_requires_eighty_percent() -> None:
    cfg = configparser.ConfigParser()
    cfg.read(UNIT_COV_CONFIG)
    assert int(cfg["report"]["fail_under"]) == 80
    omit = cfg["run"].get("omit", "")
    assert "src/integration" in omit
    assert "src/commands/chat.py" in omit
    assert "src/commands/craft.py" in omit


def test_coverage_unit_ini_scopes_cli_package() -> None:
    cfg = configparser.ConfigParser()
    cfg.read(UNIT_COV_CONFIG)
    source = cfg["run"]["source"].strip()
    assert source == "src"
    include = cfg["report"].get("include", "")
    assert "src/cli.py" in include
    assert "src/commands" in include


def test_run_unit_script_enforces_coverage_gate() -> None:
    text = RUN_UNIT.read_text(encoding="utf-8")
    assert "coverage-unit.ini" in text
    assert "--cov-fail-under=80" in text
    assert '-m "not integration"' in text
    assert "--cov=src" in text


def test_unit_script_excludes_integration_marker_only() -> None:
    text = RUN_UNIT.read_text(encoding="utf-8")
    assert '-m "not integration"' in text


def test_integration_script_runs_full_pytest() -> None:
    text = (ROOT / "scripts/docker/run-integration.sh").read_text(encoding="utf-8")
    assert "pytest -q" in text
    assert '-m "not integration"' not in text
