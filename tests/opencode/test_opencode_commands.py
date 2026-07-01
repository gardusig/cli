"""OpenCode command structure tests."""

from __future__ import annotations

from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()


def test_opencode_help_lists_domains() -> None:
    result = runner.invoke(app, ["opencode", "--help"])
    assert result.exit_code == 0
    for token in ("chat", "gh", "plan", "summarize", "code", "categorize"):
        assert token in result.stdout


def test_opencode_gh_help() -> None:
    result = runner.invoke(app, ["opencode", "gh", "--help"])
    assert result.exit_code == 0
    for cmd in ("issue", "pick", "next", "execute", "pr", "review", "draft"):
        assert cmd in result.stdout


def test_hidden_craft_alias() -> None:
    result = runner.invoke(app, ["craft", "--help"])
    assert result.exit_code == 0
    assert "issue" in result.stdout
