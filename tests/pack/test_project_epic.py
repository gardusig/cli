"""Pack tests — GitHub Projects recurrent board (epic 08)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from src.cli import app

from tests.pack.conftest import requires_docs

ROOT = Path(__file__).resolve().parents[2]
RUNNER = CliRunner()


@requires_docs
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


def test_project_spawn_seed_fixture() -> None:
    seed = ROOT / "config" / "project" / "examples" / "seed.yaml"
    assert seed.is_file()
    text = seed.read_text(encoding="utf-8")
    assert "items:" in text
    assert "docs: weekly review" in text


def test_project_lane_help() -> None:
    result = RUNNER.invoke(app, ["project", "lane", "--help"])
    assert result.exit_code == 0
    assert "issue" in result.stdout.lower()
