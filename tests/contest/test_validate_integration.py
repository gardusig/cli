"""Live Docker integration for cli contest validate."""

from __future__ import annotations

from tests.constants import ROOT

import pytest
from typer.testing import CliRunner

from src.cli import app
from src.services.docker_runtime import ensure_docker, run_docker


TOY = ROOT / "tests" / "fixtures" / "contest" / "toy"
IMAGE = "cli-contest:runner"


@pytest.mark.integration
def test_contest_validate_toy_live() -> None:
    try:
        ensure_docker()
    except RuntimeError as exc:
        pytest.skip(str(exc))

    image = run_docker(["image", "inspect", IMAGE], check=False)
    if image.returncode != 0:
        pytest.skip(
            f"{IMAGE} is built by gardusig/github-pipelines; no repo-local Dockerfile or build script is expected"
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
