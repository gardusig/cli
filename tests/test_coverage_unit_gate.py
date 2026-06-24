"""Guardrails: unit test job must enforce ≥80% coverage (Docker / CI gate)."""

from __future__ import annotations

import configparser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

UNIT_COV_CONFIG = ROOT / "coverage-unit.ini"
RUN_UNIT = ROOT / "scripts/docker/run-unit.sh"


def test_coverage_unit_ini_requires_eighty_percent() -> None:
    cfg = configparser.ConfigParser()
    cfg.read(UNIT_COV_CONFIG)
    assert int(cfg["report"]["fail_under"]) == 80
    omit = cfg["run"].get("omit", "")
    assert "gardusig_cli/integration" in omit


def test_coverage_unit_ini_scopes_cli_package() -> None:
    cfg = configparser.ConfigParser()
    cfg.read(UNIT_COV_CONFIG)
    source = cfg["run"]["source"].strip()
    assert source == "gardusig_cli"
    include = cfg["report"].get("include", "")
    assert "gardusig_cli/cli.py" in include
    assert "gardusig_cli/commands" in include


def test_run_unit_script_enforces_coverage_gate() -> None:
    text = RUN_UNIT.read_text(encoding="utf-8")
    assert "coverage-unit.ini" in text
    assert "--cov-fail-under=80" in text
    assert '-m "not integration"' in text
    assert "--cov=gardusig_cli" in text


def test_unit_script_excludes_integration_marker_only() -> None:
    text = RUN_UNIT.read_text(encoding="utf-8")
    assert '-m "not integration"' in text


def test_integration_script_runs_full_pytest() -> None:
    text = (ROOT / "scripts/docker/run-integration.sh").read_text(encoding="utf-8")
    assert "pytest -q" in text
    assert '-m "not integration"' not in text
