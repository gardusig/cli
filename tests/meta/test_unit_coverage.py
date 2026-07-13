"""Unit tests for coverage gaps outside integration packages."""

from __future__ import annotations

from tests.constants import ROOT

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from src.cli import app
from src.commands.git import _branch_preview_lines
from src.internal.read.safety import OperationKind, classify_operation
from src.services.git_shortcuts import GitShortcuts


runner = CliRunner()
PATCH = "src.services.git_shortcuts.run_git"
SNAPSHOT = "src.commands.git.git_worktree_snapshot"


def test_package_main_entrypoint() -> None:
    """src.__main__ runs the Typer app (python -m src)."""
    result = subprocess.run(
        [sys.executable, "-m", "src", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "git" in result.stdout


def test_branch_preview_lines_truncates() -> None:
    branches = [f"branch-{i}" for i in range(25)]
    lines = _branch_preview_lines("preview", branches, limit=3)
    assert lines[0] == "preview: 25"
    assert lines[1] == "  - branch-0"
    assert any("more)" in line for line in lines)


def test_classify_unknown_operation_is_gated() -> None:
    assert classify_operation("novel-op") == OperationKind.WRITE_GATED


@pytest.fixture
def snapshot() -> MagicMock:
    snap = MagicMock()
    snap.summary_lines.return_value = ["branch: feat", "dirty: true"]
    return snap


@patch.object(GitShortcuts, "reset", return_value=[])
def test_git_reset_main_only_message(mock_reset: MagicMock, snapshot: MagicMock) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "reset", "--yes", "--main-only"])
    assert result.exit_code == 0
    assert "synced with remote" in result.stdout


@patch.object(GitShortcuts, "branch_delete_all_merged", return_value=["a"])
@patch.object(GitShortcuts, "merged_branch_names", return_value=["a"])
@patch.object(GitShortcuts, "reset", return_value=[])
def test_git_reset_prune_message(
    mock_reset: MagicMock,
    _merged: MagicMock,
    mock_delete: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "reset", "--yes", "--delete-merged"])
    assert "removed 1 branch" in result.stdout
    mock_delete.assert_called_once_with(yes=True)


@patch.object(GitShortcuts, "is_dirty", return_value=True)
@patch.object(GitShortcuts, "remote_exists", return_value=True)
@patch.object(GitShortcuts, "current_branch", return_value="feat")
@patch.object(GitShortcuts, "reset", return_value=[])
def test_git_reset_discard_intent(
    _reset: MagicMock,
    _branch: MagicMock,
    _remote: MagicMock,
    _dirty: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "reset", "--yes", "--discard"])
    assert result.exit_code == 0
    assert "discard uncommitted" in result.stdout


@patch.object(GitShortcuts, "branch_delete")
def test_git_branch_delete_action(
    mock_delete: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "branch", "delete", "old", "--yes"])
    assert result.exit_code == 0
    assert "deleted" in result.stdout
    mock_delete.assert_called_once()


@patch("src.utils.process.run_git")
def test_git_branch_rename(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    result = runner.invoke(app, ["git", "branch", "rename", "new-name"])
    assert result.exit_code == 0
    assert "renamed" in result.stdout


@patch.object(GitShortcuts, "push")
@patch.object(GitShortcuts, "start", return_value="feat-push")
def test_git_start_no_prep_with_push(mock_start: MagicMock, mock_push: MagicMock) -> None:
    result = runner.invoke(
        app,
        ["git", "start", "feat-push", "--no-prep", "--push", "--yes"],
    )
    assert result.exit_code == 0
    mock_start.assert_called_once_with(
        "feat-push",
        yes=True,
        keep_ignored=False,
        prep=False,
        no_push=False,
    )


@patch.object(GitShortcuts, "stash_pop")
@patch.object(GitShortcuts, "stash_apply")
def test_git_stash_apply_and_pop(mock_apply: MagicMock, mock_pop: MagicMock) -> None:
    apply_result = runner.invoke(app, ["git", "stash", "apply", "--index", "1"])
    assert apply_result.exit_code == 0
    mock_apply.assert_called_once_with(1)
    pop_result = runner.invoke(app, ["git", "stash", "pop", "--index", "2"])
    assert pop_result.exit_code == 0
    mock_pop.assert_called_once_with(2)


@patch(PATCH)
def test_reset_all_local_deletes_every_branch(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    svc = GitShortcuts(top="/tmp/repo")
    with (
        patch.object(svc, "_prepare_leave_branch"),
        patch.object(svc, "sync_main"),
        patch.object(svc, "local_branch_names", return_value=["a", "b"]),
    ):
        deleted = svc.reset(yes=True, all_local=True)
    assert deleted == ["a", "b"]
    assert mock_run.call_count == 2


@patch(PATCH)
def test_sync_main_resets_to_best_main(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    svc = GitShortcuts(top="/tmp/repo")
    with (
        patch.object(svc, "is_dirty", return_value=False),
        patch.object(svc, "checkout_main"),
        patch.object(svc, "fetch_all"),
        patch.object(svc, "best_main_ref", return_value="origin/main"),
    ):
        svc.sync_main(yes=True, keep_ignored=True)
    assert ["reset", "--hard", "origin/main"] in [c.args[0] for c in mock_run.call_args_list]


@patch("src.commands.backup.status_cmd")
def test_backup_status_alias_calls_drive(mock_status: MagicMock) -> None:
    result = runner.invoke(app, ["backup", "status"])
    assert result.exit_code == 0
    mock_status.assert_called_once()


@patch("src.commands.backup.ingest_cmd")
def test_backup_repository_sync_alias(mock_ingest: MagicMock) -> None:
    result = runner.invoke(app, ["backup", "repository", "sync", "/tmp/repo"])
    assert result.exit_code == 0
    mock_ingest.assert_called_once_with("/tmp/repo")


@patch("src.commands.backup.list_cmd")
def test_backup_repository_list_alias(mock_list: MagicMock) -> None:
    result = runner.invoke(app, ["backup", "repository", "list"])
    assert result.exit_code == 0
    mock_list.assert_called_once_with(None)


@patch("src.commands.backup.delete_cmd")
def test_backup_repository_delete_alias(mock_delete: MagicMock) -> None:
    result = runner.invoke(app, ["backup", "repository", "delete", "/tmp/repo", "v1", "--yes"])
    assert result.exit_code == 0
    mock_delete.assert_called_once_with("/tmp/repo", "v1", yes=True)


def test_hygiene_check_dispatches_structure(monkeypatch, tmp_path: Path) -> None:
    policy = tmp_path / "policy.yaml"
    policy.write_text("allowed_extensions: [.md]\n", encoding="utf-8")
    calls: list[tuple] = []
    monkeypatch.setattr(
        "src.commands._toolkit.run_cli_command",
        lambda *args, **kwargs: calls.append((args, kwargs)) or 0,
    )
    result = runner.invoke(
        app,
        ["hygiene", "check", str(tmp_path), "--require-layout", "--policy-file", str(policy)],
    )
    assert result.exit_code == 0
    assert calls[0][0][:3] == ("structure", "check", tmp_path)
    assert calls[0][1]["extra_env"]["REQUIRE_LAYOUT"] == "1"
    assert calls[0][1]["extra_env"]["POLICY_FILE"] == str(policy.resolve())


@patch("src.commands.publish.pypi_upload_cmd")
def test_publish_pypi_upload_deprecated_alias(mock_upload: MagicMock) -> None:
    result = runner.invoke(app, ["publish", "pypi", "--yes", "--testpypi"])
    assert result.exit_code == 0
    mock_upload.assert_called_once()
    _, kwargs = mock_upload.call_args
    assert kwargs["testpypi"] is True


def test_cli_run_surfaces_external_call_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import typer
    from src.cli import run
    from src.utils.external_client import ExternalCallError

    def _boom() -> None:
        raise ExternalCallError(
            service="net",
            operation="call",
            user_message="network down",
        )

    monkeypatch.setattr("src.cli.app", _boom)
    with pytest.raises(typer.Exit) as exc_info:
        run()
    assert exc_info.value.exit_code == 1
