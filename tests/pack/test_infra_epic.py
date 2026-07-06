"""Pack tests — selective CI contracts (epic 00-infra)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from src.cli import app
from src.services import test_packages

ROOT = Path(__file__).resolve().parents[2]
RUNNER = CliRunner()

INTEGRATION_SCRIPT_PACKAGES = (
    "gh",
    "git",
    "notion",
    "drive",
    "chrome",
    "docker",
    "contest",
    "project",
    "pypi",
)


def test_infra_epic_ci_docs_exist() -> None:
    text = (ROOT / "docs" / "ci-workflows.md").read_text(encoding="utf-8")
    assert "packages resolve" in text
    assert "packages suite" in text
    assert "full_suite" in text
    assert "Epic 00 closure" in text


def test_infra_epic_script_policy_docs() -> None:
    text = (ROOT / "scripts" / "test" / "README.md").read_text(encoding="utf-8")
    assert "Nine-script policy" in text
    assert "gh.sh" in text


def test_infra_epic_registry_covers_gh() -> None:
    names = {pkg.name for pkg in test_packages.test_package_registry()}
    assert "gh" in names
    assert "git" in names
    assert "docker" in names


def test_infra_epic_integration_scripts_exist() -> None:
    scripts = ROOT / "scripts" / "test"
    for package in INTEGRATION_SCRIPT_PACKAGES:
        assert (scripts / f"{package}.sh").is_file(), package
    assert (scripts / "all.sh").is_file()
    assert (scripts / "_common.sh").is_file()


def test_infra_epic_resolve_help() -> None:
    result = RUNNER.invoke(app, ["test", "packages", "resolve", "--help"])
    assert result.exit_code == 0
    assert "--base" in result.stdout
    assert "--format" in result.stdout


def test_infra_epic_suite_contract() -> None:
    result = RUNNER.invoke(app, ["test", "packages", "suite", "--format", "json"])
    assert result.exit_code == 0
    assert "check_integration_coverage" in result.stdout
