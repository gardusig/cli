"""Contest validate with mocked runner (no live Docker)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from gardusig_cli.cli import app
from gardusig_cli.integration.contest_integration import run_all_contest_checks
from gardusig_cli.services.contest_runner import ContestValidateResult

ROOT = Path(__file__).resolve().parents[1]
TOY = ROOT / "tests" / "fixtures" / "contest" / "toy"
RUNNER = CliRunner()


@pytest.mark.integration
def test_contest_validate_mocked_pass() -> None:
    with patch("gardusig_cli.commands.contest.validate_contest", return_value=ContestValidateResult(passed=True)):
        result = RUNNER.invoke(
            app,
            [
                "contest",
                "validate",
                "--fast",
                str(TOY / "solution.cpp"),
                "--brute",
                str(TOY / "brute.py"),
                "--generator",
                str(TOY / "gen.py"),
            ],
        )
    assert result.exit_code == 0
    assert "PASS" in result.output


@pytest.mark.integration
def test_contest_validate_mocked_fail() -> None:
    with patch(
        "gardusig_cli.commands.contest.validate_contest",
        return_value=ContestValidateResult(passed=False, error="small tier outputs differ"),
    ):
        result = RUNNER.invoke(
            app,
            [
                "contest",
                "validate",
                "--fast",
                str(TOY / "solution.cpp"),
                "--brute",
                str(TOY / "brute.py"),
                "--generator",
                str(TOY / "gen.py"),
            ],
        )
    assert result.exit_code == 1
    assert "FAIL" in result.output


@pytest.mark.integration
def test_contest_integration_registry_passes() -> None:
    errors = run_all_contest_checks(ROOT)
    assert errors == [], "\n---\n".join(errors)
