"""Pack tests — hub operator smoke checks."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from src.cli import app
from src.services.gh_policy import MERGE_FORBIDDEN_MESSAGE

from tests.pack.conftest import requires_docs

ROOT = Path(__file__).resolve().parents[2]
RUNNER = CliRunner()


@requires_docs
def test_hub_operator_docs_exist() -> None:
    assert (ROOT / "docs" / "hub-operator.md").is_file()
    assert (ROOT / "docs" / "opencode.md").is_file()
    hub = (ROOT / "docs" / "hub-operator.md").read_text(encoding="utf-8")
    assert "operator-test.yml" in hub
    assert "operator-craft-plan.yml" in hub
    assert "operator-review.yml" in hub
    assert "operator-dispatch.yml" in hub


def test_deploy_help_lists_lanes() -> None:
    result = RUNNER.invoke(app, ["deploy", "--help"])
    assert result.exit_code == 0
    assert "pull-request" in result.stdout
    assert "operator" in result.stdout


def test_hub_operator_batch_manifest_exists() -> None:
    batch = ROOT / "config" / "gh" / "phase5" / "cli.batch.yaml"
    assert batch.is_file()
    text = batch.read_text(encoding="utf-8")
    assert "epic:hub-operator" in text


def test_deepseek_models_config() -> None:
    cfg = ROOT / "config" / "deepseek" / "models.yaml"
    assert cfg.is_file()
    text = cfg.read_text(encoding="utf-8")
    assert "reason" in text
    assert "chat" in text


def test_opencode_entry_registered() -> None:
    result = RUNNER.invoke(app, ["opencode", "--help"])
    assert result.exit_code == 0
    assert "chat" in result.stdout
    assert "gh" in result.stdout


def test_gh_pr_merge_blocked_by_policy() -> None:
    result = RUNNER.invoke(app, ["gh", "pr", "merge", "1"])
    assert result.exit_code != 0
    assert MERGE_FORBIDDEN_MESSAGE.splitlines()[0] in (result.stdout + result.stderr)


def test_test_packages_resolve_help() -> None:
    result = RUNNER.invoke(app, ["test", "packages", "resolve", "--help"])
    assert result.exit_code == 0
    assert "json" in result.stdout.lower() or "--format" in result.stdout
