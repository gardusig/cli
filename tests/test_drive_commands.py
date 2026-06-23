"""CLI tests for cli drive commands (local ingest + upload)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from cli.cli import app
from cli.services.backup_repository import SyncResult

runner = CliRunner()


@patch("cli.commands.drive.format_status_lines", return_value=["Repository: demo\n"])
@patch("cli.commands.drive.backup_status", return_value=[])
def test_drive_status(_status: MagicMock, _lines: MagicMock) -> None:
    result = runner.invoke(app, ["drive", "status"])
    assert result.exit_code == 0
    assert "Repository: demo" in result.stdout


@patch("cli.commands.drive.ingest_repositories")
def test_drive_ingest_all(mock_ingest: MagicMock) -> None:
    repo = Path("/tmp/demo")
    mock_ingest.return_value = [(repo, SyncResult(created=["v1"], replaced=[], failed=[]))]
    result = runner.invoke(app, ["drive", "ingest"])
    assert result.exit_code == 0
    assert "v1" in result.stdout
    mock_ingest.assert_called_once_with(None)


@patch("cli.commands.drive.ingest_repositories", side_effect=RuntimeError("no repos"))
def test_drive_ingest_failure(mock_ingest: MagicMock) -> None:
    result = runner.invoke(app, ["drive", "ingest"])
    assert result.exit_code != 0
    assert "no repos" in result.stdout
    mock_ingest.assert_called_once()


@patch("cli.commands.drive.deploy_replicas")
@patch("cli.commands.drive.ingest_repositories")
@patch("cli.commands.drive.tags_dir_path")
def test_drive_sync(
    mock_tags: MagicMock,
    mock_ingest: MagicMock,
    mock_deploy: MagicMock,
    tmp_path: Path,
) -> None:
    from cli.services.drive_sync import UploadResult

    tags_root = tmp_path / "git-tags"
    tags_root.mkdir()
    mock_tags.return_value = tags_root
    repo = Path("/tmp/demo")
    mock_ingest.return_value = [(repo, SyncResult(created=["v1"], replaced=[], failed=[]))]
    mock_deploy.return_value = [("google", UploadResult(uploaded=["demo/v1.zip"], skipped=[], failed=[]))]
    result = runner.invoke(app, ["drive", "sync"])
    assert result.exit_code == 0
    assert "Phase 1" in result.stdout
    assert "Phase 2" in result.stdout
    assert "v1" in result.stdout
    mock_ingest.assert_called_once()
    mock_deploy.assert_called_once()


@patch("cli.commands.drive.tags_dir_path")
def test_drive_sync_missing_local_dir(mock_tags: MagicMock) -> None:
    mock_tags.return_value = Path("/no/such/git-tags")
    result = runner.invoke(app, ["drive", "sync"])
    assert result.exit_code != 0
    assert "not found" in result.stdout.lower()


@patch("cli.commands.drive.tags_dir_path")
def test_drive_upload_missing_local_dir(mock_tags: MagicMock) -> None:
    mock_tags.return_value = Path("/no/such/git-tags")
    result = runner.invoke(app, ["drive", "upload"])
    assert result.exit_code != 0
    assert "not found" in result.stdout.lower()


@patch("cli.commands.drive.deploy_replicas")
@patch("cli.commands.drive.tags_dir_path")
def test_drive_upload_success(
    mock_tags: MagicMock,
    mock_deploy: MagicMock,
    tmp_path: Path,
) -> None:
    from cli.services.drive_sync import UploadResult

    tags_root = tmp_path / "git-tags"
    tags_root.mkdir()
    mock_tags.return_value = tags_root
    mock_deploy.return_value = [("google", UploadResult(uploaded=["demo/v1.zip"], skipped=[], failed=[]))]
    result = runner.invoke(app, ["drive", "upload", "google"])
    assert result.exit_code == 0
    assert "demo/v1.zip" in result.stdout
    mock_deploy.assert_called_once()


@patch("cli.commands.drive.list_downloaded_tags", return_value=["v1", "v2"])
@patch("cli.commands.drive.resolve_repo_path")
def test_drive_list_tags(mock_resolve: MagicMock, _tags: MagicMock, tmp_path: Path) -> None:
    mock_resolve.return_value = tmp_path / "demo"
    result = runner.invoke(app, ["drive", "list", str(tmp_path / "demo")])
    assert result.exit_code == 0
    assert "v1" in result.stdout
    assert "v2" in result.stdout


@patch("cli.commands.drive.delete_repo_tag")
@patch("cli.commands.drive.git_worktree_snapshot")
@patch("cli.commands.drive.resolve_repo_path")
def test_drive_delete_with_yes(
    mock_resolve: MagicMock,
    mock_snapshot: MagicMock,
    mock_delete: MagicMock,
    tmp_path: Path,
) -> None:
    repo = tmp_path / "demo"
    repo.mkdir()
    mock_resolve.return_value = repo
    mock_snapshot.return_value.summary_lines.return_value = ["branch: main"]
    mock_delete.return_value = repo / "v1.zip"
    result = runner.invoke(app, ["drive", "delete", str(repo), "v1", "--yes"])
    assert result.exit_code == 0
    assert "deleted" in result.stdout
