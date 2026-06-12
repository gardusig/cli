"""CLI tests for shuttle drive commands (local ingest + upload)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from shuttle.cli import app
from shuttle.services.backup_repository import SyncResult

runner = CliRunner()


@patch("shuttle.commands.drive.format_status_lines", return_value=["Repository: demo\n"])
@patch("shuttle.commands.drive.backup_status", return_value=[])
def test_drive_status(_status: MagicMock, _lines: MagicMock) -> None:
    result = runner.invoke(app, ["drive", "status"])
    assert result.exit_code == 0
    assert "Repository: demo" in result.stdout


@patch("shuttle.commands.drive.ingest_repositories")
def test_drive_ingest_all(mock_ingest: MagicMock) -> None:
    repo = Path("/tmp/demo")
    mock_ingest.return_value = [(repo, SyncResult(created=["v1"], replaced=[], failed=[]))]
    result = runner.invoke(app, ["drive", "ingest"])
    assert result.exit_code == 0
    assert "v1" in result.stdout
    mock_ingest.assert_called_once_with(None)


@patch("shuttle.commands.drive.ingest_repositories", side_effect=RuntimeError("no repos"))
def test_drive_ingest_failure(mock_ingest: MagicMock) -> None:
    result = runner.invoke(app, ["drive", "ingest"])
    assert result.exit_code != 0
    assert "no repos" in result.stdout
    mock_ingest.assert_called_once()


@patch("shuttle.commands.drive.sync_all")
@patch("shuttle.commands.drive.tags_dir_path")
@patch("shuttle.commands.drive.load_config")
@patch("shuttle.commands.drive._enabled_providers")
def test_drive_sync(
    mock_providers: MagicMock,
    mock_cfg: MagicMock,
    mock_tags: MagicMock,
    mock_sync: MagicMock,
    tmp_path: Path,
) -> None:
    from shuttle.services.drive_sync import DriveSyncResult, UploadResult

    tags_root = tmp_path / "git-tags"
    tags_root.mkdir()
    mock_tags.return_value = tags_root
    mock_providers.return_value = [("google", MagicMock(), "git-tags")]
    repo = Path("/tmp/demo")
    mock_sync.return_value = DriveSyncResult(
        ingest=[(repo, SyncResult(created=["v1"], replaced=[], failed=[]))],
        uploads=[("google", UploadResult(uploaded=["demo/v1.zip"], skipped=[], failed=[]))],
    )
    result = runner.invoke(app, ["drive", "sync"])
    assert result.exit_code == 0
    assert "Phase 1" in result.stdout
    assert "Phase 2" in result.stdout
    assert "v1" in result.stdout
    mock_sync.assert_called_once()


@patch("shuttle.commands.drive.tags_dir_path")
def test_drive_sync_missing_local_dir(mock_tags: MagicMock) -> None:
    mock_tags.return_value = Path("/no/such/git-tags")
    result = runner.invoke(app, ["drive", "sync"])
    assert result.exit_code != 0
    assert "not found" in result.stdout.lower()


@patch("shuttle.commands.drive.upload_missing")
@patch("shuttle.commands.drive.tags_dir_path")
@patch("shuttle.commands.drive.load_config")
def test_drive_upload_missing_local_dir(
    mock_cfg: MagicMock,
    mock_tags: MagicMock,
    _upload: MagicMock,
) -> None:
    mock_tags.return_value = Path("/no/such/git-tags")
    result = runner.invoke(app, ["drive", "upload"])
    assert result.exit_code != 0
    assert "not found" in result.stdout.lower()
