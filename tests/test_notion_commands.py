"""CLI tests for shuttle notion ingest/deploy/sync/cleanup stubs."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from shuttle.cli import app

runner = CliRunner()


def test_notion_ingest_requires_token() -> None:
    result = runner.invoke(app, ["notion", "ingest"])
    assert result.exit_code != 0
    assert "NOTION_TOKEN" in result.stdout


def test_notion_ingest_stub(monkeypatch) -> None:
    monkeypatch.setenv("NOTION_TOKEN", "test-token")
    with patch("shuttle.commands.notion.load_config") as mock_cfg:
        mock_cfg.return_value.notion.database_id = "db-123"
        result = runner.invoke(app, ["notion", "ingest"])
    assert result.exit_code != 0
    assert "not implemented" in result.stdout.lower()


def test_notion_cleanup_requires_yes(monkeypatch) -> None:
    monkeypatch.setenv("NOTION_TOKEN", "test-token")
    with patch("shuttle.commands.notion.load_config") as mock_cfg:
        mock_cfg.return_value.notion.database_id = "db-123"
        result = runner.invoke(app, ["notion", "cleanup"])
    assert result.exit_code != 0
    assert "non-interactive" in result.stdout.lower() or "confirm" in result.stdout.lower()


def test_notion_help_lists_commands() -> None:
    result = runner.invoke(app, ["notion", "--help"])
    assert result.exit_code == 0
    assert "ingest" in result.stdout
    assert "deploy" in result.stdout
    assert "sync" in result.stdout
    assert "cleanup" in result.stdout


def test_notion_legacy_download_alias(monkeypatch) -> None:
    monkeypatch.setenv("NOTION_TOKEN", "test-token")
    with patch("shuttle.commands.notion.load_config") as mock_cfg:
        mock_cfg.return_value.notion.database_id = "db-123"
        result = runner.invoke(app, ["notion", "download"])
    assert result.exit_code != 0
    assert "not implemented" in result.stdout.lower()
