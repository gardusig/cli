"""CLI smoke tests for contest commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from shuttle.cli import app
from shuttle.services.contest_runner import ContestValidateResult

ROOT = Path(__file__).resolve().parents[1]
TOY = ROOT / "tests" / "fixtures" / "contest" / "toy"


@patch("shuttle.commands.contest.validate_contest")
def test_contest_validate_cli_pass(mock_validate) -> None:
    mock_validate.return_value = ContestValidateResult(passed=True)
    runner = CliRunner()
    result = runner.invoke(
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


@patch("shuttle.commands.contest.validate_contest")
def test_contest_validate_cli_fail(mock_validate) -> None:
    mock_validate.return_value = ContestValidateResult(
        passed=False,
        error="small tier outputs differ",
    )
    runner = CliRunner()
    result = runner.invoke(
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
