"""CLI tests for cli notion ingest/deploy/sync/cleanup."""

from __future__ import annotations

from tests.constants import ROOT

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from gardusig_cli.cli import app
from gardusig_cli.integration.workspaces import notion_task_fixture_dir
from gardusig_cli.services.notion_sync import NotionSyncResult

runner = CliRunner()
FIXTURE_ROOT = notion_task_fixture_dir()


def test_notion_ingest_requires_token(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    with patch("gardusig_cli.commands.notion.require_notion_token", side_effect=RuntimeError("NOTION_TOKEN")):
        result = runner.invoke(app, ["notion", "ingest"])
    assert result.exit_code != 0
    assert "NOTION_TOKEN" in result.stdout


def test_notion_ingest_success(monkeypatch) -> None:
    monkeypatch.setenv("NOTION_TOKEN", "test-token")
    with (
        patch("gardusig_cli.commands.notion.load_config") as mock_cfg,
        patch("gardusig_cli.commands.notion.export_tasks") as mock_export,
        patch("gardusig_cli.commands.notion.notion_task_root") as mock_root,
        patch("gardusig_cli.commands.notion.notion_pairs_file") as mock_manifest,
    ):
        mock_cfg.return_value.notion.database_id = "db-123"
        mock_root.return_value = FIXTURE_ROOT
        mock_manifest.return_value = FIXTURE_ROOT / "tasks.pairs.json"
        mock_export.return_value = NotionSyncResult(processed=1)
        result = runner.invoke(app, ["notion", "ingest"])
    assert result.exit_code == 0
    assert "ingested" in result.stdout


def test_notion_deploy_requires_manifest(monkeypatch) -> None:
    monkeypatch.setenv("NOTION_TOKEN", "test-token")
    with (
        patch("gardusig_cli.commands.notion.load_config") as mock_cfg,
        patch("gardusig_cli.commands.notion.notion_task_root") as mock_root,
        patch("gardusig_cli.commands.notion.notion_pairs_file") as mock_manifest,
    ):
        mock_cfg.return_value.notion.database_id = "db-123"
        mock_root.return_value = Path("/tmp/missing-tasks")
        mock_manifest.return_value = Path("/tmp/missing-tasks/tasks.pairs.json")
        result = runner.invoke(app, ["notion", "deploy", "--yes", "--no-cleanup"])
    assert result.exit_code != 0
    assert "pairs build" in result.stdout.lower() or "manifest" in result.stdout.lower()


def test_notion_cleanup_requires_yes(monkeypatch) -> None:
    monkeypatch.setenv("NOTION_TOKEN", "test-token")
    with patch("gardusig_cli.commands.notion.load_config") as mock_cfg:
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
    assert "pairs" in result.stdout


def test_notion_pairs_build(monkeypatch, tmp_path: Path) -> None:
    task_root = tmp_path / "tasks"
    (task_root / "header").mkdir(parents=True)
    (task_root / "body").mkdir(parents=True)
    (task_root / "header" / "a.yaml").write_text("name: Task A\n", encoding="utf-8")
    (task_root / "body" / "a.md").write_text("# A\n", encoding="utf-8")
    with (
        patch("gardusig_cli.commands.notion.notion_task_root", return_value=task_root),
        patch("gardusig_cli.commands.notion.notion_pairs_file", return_value=task_root / "tasks.pairs.json"),
        patch(
            "gardusig_cli.commands.notion.build_pairs_manifest",
            return_value=NotionSyncResult(processed=1),
        ),
        patch("gardusig_cli.commands.notion.load_pairs", return_value=[]),
        patch(
            "gardusig_cli.commands.notion.pair_deploy_rollout",
            return_value=MagicMock(enabled=["Task A"], disabled=[], broken=[]),
        ),
    ):
        result = runner.invoke(app, ["notion", "pairs", "build"])
    assert result.exit_code == 0
    assert "built" in result.stdout


def test_notion_legacy_download_alias(monkeypatch) -> None:
    monkeypatch.setenv("NOTION_TOKEN", "test-token")
    with (
        patch("gardusig_cli.commands.notion.load_config") as mock_cfg,
        patch("gardusig_cli.commands.notion.export_tasks") as mock_export,
        patch("gardusig_cli.commands.notion.notion_task_root") as mock_root,
        patch("gardusig_cli.commands.notion.notion_pairs_file") as mock_manifest,
    ):
        mock_cfg.return_value.notion.database_id = "db-123"
        mock_root.return_value = FIXTURE_ROOT
        mock_manifest.return_value = FIXTURE_ROOT / "tasks.pairs.json"
        mock_export.return_value = NotionSyncResult(processed=0)
        result = runner.invoke(app, ["notion", "download"])
    assert result.exit_code == 0


def test_notion_deploy_success_with_warnings(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("NOTION_TOKEN", "test-token")
    manifest = tmp_path / "tasks.pairs.json"
    manifest.write_text("[]\n", encoding="utf-8")
    with (
        patch("gardusig_cli.commands.notion.load_config") as mock_cfg,
        patch("gardusig_cli.commands.notion.import_tasks") as mock_import,
        patch("gardusig_cli.commands.notion.notion_task_root", return_value=tmp_path),
        patch("gardusig_cli.commands.notion.notion_pairs_file", return_value=manifest),
    ):
        mock_cfg.return_value.notion.database_id = "db-123"
        mock_cfg.return_value.notion.cleanup_before_deploy = False
        mock_import.return_value = NotionSyncResult(
            processed=2,
            skipped=1,
            warnings=["header without body: metadata/x.yaml"],
        )
        result = runner.invoke(app, ["notion", "deploy", "--yes", "--no-cleanup"])
    assert result.exit_code == 0
    assert "deployed" in result.stdout
    assert "warning" in result.stdout


def test_notion_sync_runs_both_phases(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("NOTION_TOKEN", "test-token")
    manifest = tmp_path / "tasks.pairs.json"
    manifest.write_text("[]\n", encoding="utf-8")
    with (
        patch("gardusig_cli.commands.notion.load_config") as mock_cfg,
        patch("gardusig_cli.commands.notion.export_tasks") as mock_export,
        patch("gardusig_cli.commands.notion.import_tasks") as mock_import,
        patch("gardusig_cli.commands.notion.notion_task_root", return_value=tmp_path),
        patch("gardusig_cli.commands.notion.notion_pairs_file", return_value=manifest),
    ):
        mock_cfg.return_value.notion.database_id = "db-123"
        mock_cfg.return_value.notion.cleanup_before_deploy = False
        mock_export.return_value = NotionSyncResult(processed=1)
        mock_import.return_value = NotionSyncResult(processed=1, skipped=0)
        result = runner.invoke(app, ["notion", "sync", "--yes", "--no-cleanup"])
    assert result.exit_code == 0
    assert "Phase 1" in result.stdout
    assert "Phase 2" in result.stdout


def test_notion_cleanup_with_yes(monkeypatch) -> None:
    monkeypatch.setenv("NOTION_TOKEN", "test-token")
    with (
        patch("gardusig_cli.commands.notion.load_config") as mock_cfg,
        patch("gardusig_cli.commands.notion.cleanup_board") as mock_cleanup,
    ):
        mock_cfg.return_value.notion.database_id = "db-123"
        mock_cleanup.return_value = NotionSyncResult(processed=3)
        result = runner.invoke(app, ["notion", "cleanup", "--yes"])
    assert result.exit_code == 0
    assert "archived" in result.stdout
