"""Pack tests — selective CI contracts (epic 00-infra)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from src.cli import app
from src.services import test_packages

ROOT = Path(__file__).resolve().parents[2]
RUNNER = CliRunner()


def test_infra_epic_ci_docs_exist() -> None:
    text = (ROOT / "docs" / "ci-workflows.md").read_text(encoding="utf-8")
    assert "packages resolve" in text
    assert "packages suite" in text
    assert "full_suite" in text


def test_infra_epic_registry_covers_gh() -> None:
    names = {pkg.name for pkg in test_packages.test_package_registry()}
    assert "gh" in names
    assert "git" in names
    assert "docker" in names


def test_infra_epic_resolve_help() -> None:
    result = RUNNER.invoke(app, ["test", "packages", "resolve", "--help"])
    assert result.exit_code == 0
    assert "--base" in result.stdout
    assert "--format" in result.stdout
