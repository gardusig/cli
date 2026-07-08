"""Pack tests — GitHub hub transport (epic 11)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from src.cli import app

from tests.pack.conftest import requires_docs

ROOT = Path(__file__).resolve().parents[2]
RUNNER = CliRunner()


@requires_docs
def test_gh_hub_epic_docs_exist() -> None:
    text = (ROOT / "docs" / "gh.md").read_text(encoding="utf-8")
    assert "Transport parity" in text
    assert "issue context" in text
    assert "composed REST" in text


def test_gh_hub_epic_batch_manifest() -> None:
    batch = ROOT / "config" / "gh" / "phase5" / "cli.batch.yaml"
    assert "epic:11-gh-hub" in batch.read_text(encoding="utf-8")


def test_gh_transport_help() -> None:
    result = RUNNER.invoke(app, ["gh", "--help"])
    assert result.exit_code == 0
    assert "--transport" in result.stdout


def test_gh_issue_context_help() -> None:
    result = RUNNER.invoke(app, ["gh", "issue", "context", "--help"])
    assert result.exit_code == 0
    assert "context" in result.stdout.lower()
