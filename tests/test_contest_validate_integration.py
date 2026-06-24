"""Live Docker integration for cli contest validate."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cli.cli import app
from cli.services.docker_runtime import ensure_docker

ROOT = Path(__file__).resolve().parents[1]
TOY = ROOT / "tests" / "fixtures" / "contest" / "toy"
IMAGE = "cli-contest:runner"


@pytest.mark.integration
def test_contest_validate_toy_live() -> None:
    try:
        ensure_docker()
    except RuntimeError as exc:
        pytest.fail(str(exc))

    build_script = ROOT / "scripts" / "docker" / "build-contest-image.sh"
    subprocess.run([str(build_script)], check=True, cwd=ROOT)

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
            "--timeout",
            "10",
            "--memory-mb",
            "256",
            "--image",
            IMAGE,
        ],
    )

    assert result.exit_code == 0, result.output
    assert "PASS" in result.output


@pytest.mark.integration
def test_contest_help() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["contest", "--help"])
    assert result.exit_code == 0
    assert "validate" in result.output
