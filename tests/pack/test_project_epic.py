"""Pack tests — GitHub Projects recurrent board (epic 08)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from src.cli import app

ROOT = Path(__file__).resolve().parents[2]
RUNNER = CliRunner()


def test_project_epic_docs_exist() -> None:
    assert (ROOT / "docs" / "project.md").is_file()
    text = (ROOT / "docs" / "project.md").read_text(encoding="utf-8")
    assert "recurrence" in text
    assert "auto_link" in text


def test_project_epic_batch_manifest() -> None:
    batch = ROOT / "config" / "gh" / "phase5" / "cli.batch.yaml"
    assert "epic:08-projects" in batch.read_text(encoding="utf-8")


def test_project_recurrence_help() -> None:
    result = RUNNER.invoke(app, ["project", "recurrence", "--help"])
    assert result.exit_code == 0
    assert "check" in result.stdout
    assert "advance" in result.stdout
