"""OpenCode command structure tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()
OPENCODE_PATCH = "src.commands.opencode_cmd.OpenCodeProvider"


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


@patch(OPENCODE_PATCH)
def test_opencode_tier_commands(mock_provider_cls: MagicMock) -> None:
    mock_provider_cls.return_value.run_prompt.return_value = "ok"
    for args in (
        ["opencode", "plan", "reason this"],
        ["opencode", "summarize", "long text"],
        ["opencode", "code", "implement x"],
        ["opencode", "code", "implement x", "--mode", "chat"],
        ["opencode", "categorize", "bucket items"],
    ):
        result = runner.invoke(app, args)
        assert result.exit_code == 0
        assert "ok" in result.stdout


def test_hidden_craft_alias() -> None:
    result = runner.invoke(app, ["craft", "--help"])
    assert result.exit_code == 0
    assert "issue" in result.stdout
