"""Workflow shortcuts: prep, kickoff, land."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from shuttle.cli import app
from shuttle.services.git_shortcuts import GitShortcuts

runner = CliRunner()
SNAPSHOT = "shuttle.commands.git.git_worktree_snapshot"


@pytest.fixture
def snapshot() -> MagicMock:
    snap = MagicMock()
    snap.summary_lines.return_value = ["branch: main", "dirty: false"]
    return snap


@patch.object(GitShortcuts, "prep")
def test_git_prep_requires_yes(mock_prep: MagicMock) -> None:
    result = runner.invoke(app, ["git", "prep"])
    assert result.exit_code != 0
    mock_prep.assert_not_called()


@patch.object(GitShortcuts, "prep")
def test_git_prep_with_yes(mock_prep: MagicMock, snapshot: MagicMock) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "prep", "--yes"])
    assert result.exit_code == 0
    assert "prep complete" in result.stdout
    assert "intent: checkout main" in result.stdout
    mock_prep.assert_called_once_with(yes=True, keep_ignored=False)


@patch.object(GitShortcuts, "kickoff", return_value="issue-9-docker")
@patch.object(GitShortcuts, "local_branch_names", return_value=[])
def test_git_kickoff_with_yes(
    _branches: MagicMock,
    mock_kickoff: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "kickoff", "issue-9-docker", "--yes"])
    assert result.exit_code == 0
    assert "kickoff" in result.stdout
    mock_kickoff.assert_called_once_with("issue-9-docker", yes=True, keep_ignored=False)


@patch.object(GitShortcuts, "land", return_value=["feat-a"])
def test_git_land_with_yes(mock_land: MagicMock, snapshot: MagicMock) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "land", "--yes"])
    assert result.exit_code == 0
    assert "landed" in result.stdout
    mock_land.assert_called_once_with(yes=True, all_local=False, keep_ignored=False)


@patch.object(GitShortcuts, "land")
def test_git_land_all_local(mock_land: MagicMock, snapshot: MagicMock) -> None:
    mock_land.return_value = ["a", "b"]
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "land", "--yes", "--all-local"])
    assert result.exit_code == 0
    mock_land.assert_called_once_with(yes=True, all_local=True, keep_ignored=False)
