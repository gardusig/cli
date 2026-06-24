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
    assert "cli/integration" in omit


def test_coverage_unit_ini_scopes_cli_package() -> None:
    cfg = configparser.ConfigParser()
    cfg.read(UNIT_COV_CONFIG)
    source = cfg["run"]["source"].strip()
    assert source == "cli"
    include = cfg["report"].get("include", "")
    assert "cli/cli.py" in include
    assert "cli/commands" in include


def test_run_unit_script_enforces_coverage_gate() -> None:
    text = RUN_UNIT.read_text(encoding="utf-8")
    assert "coverage-unit.ini" in text
    assert "--cov-fail-under=80" in text
    assert '-m "not integration"' not in text
    assert "--cov=cli" in text


def test_test_scripts_do_not_deselect_pytest_markers() -> None:
    scripts = [
        ROOT / "scripts/docker/run-unit.sh",
        ROOT / "scripts/docker/run-integration.sh",
    ]
    for path in scripts:
        text = path.read_text(encoding="utf-8")
        assert "-m " not in text, f"{path} must not filter pytest markers"
