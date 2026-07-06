"""Pack tests — Docker CLI roadmap (epic 12)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from src.cli import app

from tests.pack.conftest import requires_docs

ROOT = Path(__file__).resolve().parents[2]
RUNNER = CliRunner()


@requires_docs
def test_docker_epic_docs_exist() -> None:
    text = (ROOT / "docs" / "docker.md").read_text(encoding="utf-8")
    assert "Command matrix" in text
    assert "container-delete" in text
    assert "cli-contest:runner" in text


def test_docker_epic_help() -> None:
    result = RUNNER.invoke(app, ["docker", "--help"])
    assert result.exit_code == 0
    assert "ps" in result.stdout
    assert "reset" in result.stdout


def test_docker_json_format_help() -> None:
    result = RUNNER.invoke(app, ["docker", "ps", "--help"])
    assert result.exit_code == 0
    assert "--format" in result.stdout
