"""CLI tests for cli drive commands (local ingest + upload)."""

from __future__ import annotations

from tests.constants import ROOT

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from src.cli import app
from src.services.backup_repository import SyncResult

runner = CliRunner()


@patch("src.commands.drive.format_status_lines", return_value=["Repository: demo\n"])
@patch("src.commands.drive.backup_status", return_value=[])
def test_drive_status(_status: MagicMock, _lines: MagicMock) -> None:
    result = runner.invoke(app, ["drive", "status"])
    assert result.exit_code == 0
    assert "Repository: demo" in result.stdout


@patch("src.commands.drive.ingest_repositories")
def test_drive_ingest_all(mock_ingest: MagicMock) -> None:
    repo = Path("/tmp/demo")
    mock_ingest.return_value = [(repo, SyncResult(created=["v1"], replaced=[], failed=[]))]
    result = runner.invoke(app, ["drive", "ingest"])
    assert result.exit_code == 0
    assert "v1" in result.stdout
    mock_ingest.assert_called_once_with(None)


@patch("src.commands.drive.ingest_repositories", side_effect=RuntimeError("no repos"))
def test_drive_ingest_failure(mock_ingest: MagicMock) -> None:
    result = runner.invoke(app, ["drive", "ingest"])
    assert result.exit_code != 0
    assert "no repos" in result.stdout
    mock_ingest.assert_called_once()


@patch("src.commands.drive.deploy_replicas")
@patch("src.commands.drive.plan_ingest_repositories")
@patch("src.commands.drive.tags_dir_path")
def test_drive_sync_dry_run_json(
    mock_tags: MagicMock,
    mock_plan: MagicMock,
    mock_deploy: MagicMock,
    tmp_path: Path,
) -> None:
    from src.services.drive_sync import UploadResult

    tags_root = tmp_path / "git-tags"
    tags_root.mkdir()
    mock_tags.return_value = tags_root
    repo = Path("/tmp/demo")
    mock_plan.return_value = [(repo, SyncResult(created=["v2"], replaced=[], failed=[]))]
    mock_deploy.return_value = [("google", UploadResult(uploaded=["demo/v2.zip"], dry_run=True))]
    result = runner.invoke(app, ["drive", "sync", "--dry-run", "--format", "json"])
    assert result.exit_code == 0
    assert '"dry_run": true' in result.stdout
    assert "v2" in result.stdout
    mock_plan.assert_called_once()
    mock_deploy.assert_called_once()


@patch("src.commands.drive.preflight_replicas")
@patch("src.commands.drive.plan_ingest_repositories")
@patch("src.commands.drive.tags_dir_path")
def test_drive_sync_status_json(
    mock_tags: MagicMock,
    mock_plan: MagicMock,
    mock_preflight: MagicMock,
    tmp_path: Path,
) -> None:
    from src.services.drive_sync import ReplicaPreflight

    tags_root = tmp_path / "git-tags"
    tags_root.mkdir()
    mock_tags.return_value = tags_root
    repo = Path("/tmp/demo")
    mock_plan.return_value = [(repo, SyncResult(created=["v2"], replaced=[], failed=[]))]
    mock_preflight.return_value = [
        ReplicaPreflight(name="google", local_count=2, remote_count=1, missing_remote=["demo/v2.zip"])
    ]
    result = runner.invoke(app, ["drive", "sync", "--status", "--format", "json"])
    assert result.exit_code == 0
    assert '"status": true' in result.stdout
    assert "missing_remote" in result.stdout
    mock_plan.assert_called_once()
    mock_preflight.assert_called_once()


@patch("src.commands.drive.deploy_replicas")
@patch("src.commands.drive.ingest_repositories")
@patch("src.commands.drive.tags_dir_path")
def test_drive_sync_no_strict_continues_on_ingest_failure(
    mock_tags: MagicMock,
    mock_ingest: MagicMock,
    mock_deploy: MagicMock,
    tmp_path: Path,
) -> None:
    from src.services.drive_sync import UploadResult

    tags_root = tmp_path / "git-tags"
    tags_root.mkdir()
    mock_tags.return_value = tags_root
    repo = Path("/tmp/demo")
    mock_ingest.return_value = [
        (repo, SyncResult(created=[], replaced=[], failed=[("v1", "zip failed")]))
    ]
    mock_deploy.return_value = [("google", UploadResult(uploaded=["demo/v1.zip"], skipped=[], failed=[]))]
    result = runner.invoke(app, ["drive", "sync", "--no-strict"])
    assert result.exit_code == 0
    mock_deploy.assert_called_once()


@patch("src.commands.drive.deploy_replicas")
@patch("src.commands.drive.ingest_repositories")
@patch("src.commands.drive.tags_dir_path")
def test_drive_sync(
    mock_tags: MagicMock,
    mock_ingest: MagicMock,
    mock_deploy: MagicMock,
    tmp_path: Path,
) -> None:
    from src.services.drive_sync import UploadResult

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


@patch("src.commands.drive.tags_dir_path")
def test_drive_sync_missing_local_dir(mock_tags: MagicMock) -> None:
    mock_tags.return_value = Path("/no/such/git-tags")
    result = runner.invoke(app, ["drive", "sync"])
    assert result.exit_code != 0
    assert "not found" in result.stdout.lower()


@patch("src.commands.drive.tags_dir_path")
def test_drive_upload_missing_local_dir(mock_tags: MagicMock) -> None:
    mock_tags.return_value = Path("/no/such/git-tags")
    result = runner.invoke(app, ["drive", "upload"])
    assert result.exit_code != 0
    assert "not found" in result.stdout.lower()


@patch("src.commands.drive.deploy_replicas")
@patch("src.commands.drive.tags_dir_path")
def test_drive_upload_success(
    mock_tags: MagicMock,
    mock_deploy: MagicMock,
    tmp_path: Path,
) -> None:
    from src.services.drive_sync import UploadResult

    tags_root = tmp_path / "git-tags"
    tags_root.mkdir()
    mock_tags.return_value = tags_root
    mock_deploy.return_value = [("google", UploadResult(uploaded=["demo/v1.zip"], skipped=[], failed=[]))]
    result = runner.invoke(app, ["drive", "upload", "google"])
    assert result.exit_code == 0
    assert "demo/v1.zip" in result.stdout
    mock_deploy.assert_called_once()


@patch("src.commands.drive.download_replicas")
@patch("src.commands.drive.tags_dir_path")
def test_drive_download_json(
    mock_tags: MagicMock,
    mock_download: MagicMock,
    tmp_path: Path,
) -> None:
    from src.services.drive_sync import DownloadResult

    tags_root = tmp_path / "git-tags"
    tags_root.mkdir()
    mock_tags.return_value = tags_root
    mock_download.return_value = [("google", DownloadResult(downloaded=["demo/v1.zip"]))]
    result = runner.invoke(app, ["drive", "download", "google", "--format", "json"])
    assert result.exit_code == 0
    assert "demo/v1.zip" in result.stdout
    assert '"dry_run": false' in result.stdout


@patch("src.commands.drive.deploy_replicas")
@patch("src.commands.drive.tags_dir_path")
def test_drive_upload_dry_run(
    mock_tags: MagicMock,
    mock_deploy: MagicMock,
    tmp_path: Path,
) -> None:
    from src.services.drive_sync import UploadResult

    tags_root = tmp_path / "git-tags"
    tags_root.mkdir()
    mock_tags.return_value = tags_root
    mock_deploy.return_value = [("google", UploadResult(uploaded=["demo/v1.zip"], dry_run=True))]
    result = runner.invoke(app, ["drive", "upload", "--dry-run"])
    assert result.exit_code == 0
    mock_deploy.assert_called_once()
    assert mock_deploy.call_args.kwargs.get("dry_run") is True


@patch("src.commands.drive.deploy_replicas")
@patch("src.commands.drive.tags_dir_path")
def test_drive_upload_failure_exit_code(
    mock_tags: MagicMock,
    mock_deploy: MagicMock,
    tmp_path: Path,
) -> None:
    from src.services.drive_sync import UploadResult

    tags_root = tmp_path / "git-tags"
    tags_root.mkdir()
    mock_tags.return_value = tags_root
    mock_deploy.return_value = [
        ("google", UploadResult(failed=[("demo/v1.zip", "network")]))
    ]
    result = runner.invoke(app, ["drive", "upload"])
    assert result.exit_code == 1


@patch("src.commands.drive.list_downloaded_tags", return_value=["v1", "v2"])
@patch("src.commands.drive.resolve_repo_path")
def test_drive_list_tags(mock_resolve: MagicMock, _tags: MagicMock, tmp_path: Path) -> None:
    mock_resolve.return_value = tmp_path / "demo"
    result = runner.invoke(app, ["drive", "list", str(tmp_path / "demo")])
    assert result.exit_code == 0
    assert "v1" in result.stdout
    assert "v2" in result.stdout


@patch("src.commands.drive.delete_repo_tag")
@patch("src.commands.drive.git_worktree_snapshot")
@patch("src.commands.drive.resolve_repo_path")
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
