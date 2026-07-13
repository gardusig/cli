"""Pack tests — selective CI contracts (epic 00-infra)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from src.cli import app
from src.services import test_packages

from tests.pack.conftest import requires_docs

ROOT = Path(__file__).resolve().parents[2]
RUNNER = CliRunner()


@requires_docs
def test_infra_epic_ci_docs_exist() -> None:
    text = (ROOT / "docs" / "ci-workflows.md").read_text(encoding="utf-8")
    assert "pull-request.yaml" in text
    assert "version-check" in text
    assert "unit-test" in text
    assert "CI_UNIT_TIMEOUT" in text


def test_infra_epic_registry_covers_core_packages() -> None:
    names = {pkg.name for pkg in test_packages.test_package_registry()}
    assert "git" in names
    assert "docker" in names
    assert "notion" in names


def test_infra_epic_pipeline_scripts_exist() -> None:
    assert (ROOT / "scripts" / "pull-request" / "version-check.sh").is_file()
    assert (ROOT / "scripts" / "pull-request" / "set-version.sh").is_file()
    assert (ROOT / "scripts" / "release" / "pypi-release.sh").is_file()
    common = (ROOT / "scripts" / "_common.sh").read_text(encoding="utf-8")
    assert "CI_UNIT_TIMEOUT" in common
    assert "stage_run_with_timeout" in common


def test_infra_epic_resolve_help() -> None:
    result = RUNNER.invoke(app, ["test", "packages", "resolve", "--help"])
    assert result.exit_code == 0
    assert "--base" in result.stdout
    assert "--format" in result.stdout


def test_infra_epic_suite_contract() -> None:
    result = RUNNER.invoke(app, ["test", "packages", "suite", "--format", "json"])
    assert result.exit_code == 0
    assert "integration-smoke" in result.stdout


def test_infra_epic_git_deploy_help() -> None:
    result = RUNNER.invoke(app, ["git", "deploy", "--help"])
    assert result.exit_code == 0
    assert "tag" in result.stdout.lower()
