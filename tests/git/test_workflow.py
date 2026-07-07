"""Workflow shortcuts: reset, start, push."""

from __future__ import annotations

from tests.constants import ROOT

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from src.cli import app
from src.services.git_shortcuts import GitPushPlan, GitPushResult, GitShortcuts

runner = CliRunner()
SNAPSHOT = "src.commands.git.git_worktree_snapshot"


@pytest.fixture
def snapshot() -> MagicMock:
    snap = MagicMock()
    snap.summary_lines.return_value = ["branch: main", "dirty: false"]
    return snap


@patch.object(GitShortcuts, "reset")
def test_git_reset_requires_yes(mock_reset: MagicMock) -> None:
    result = runner.invoke(app, ["git", "reset"])
    assert result.exit_code != 0
    mock_reset.assert_not_called()


@patch.object(GitShortcuts, "reset", return_value=[])
def test_git_reset_main_only_with_yes(mock_reset: MagicMock, snapshot: MagicMock) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "reset", "--yes", "--main-only"])
    assert result.exit_code == 0
    assert "reset" in result.stdout
    mock_reset.assert_called_once_with(
        yes=True,
        keep_ignored=False,
        main_only=True,
        branch_message=".",
        discard=False,
    )


@patch.object(GitShortcuts, "start", return_value="issue-9-docker")
@patch.object(GitShortcuts, "local_branch_names", return_value=[])
def test_git_start_with_yes(
    _branches: MagicMock,
    mock_start: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "start", "issue-9-docker", "--yes"])
    assert result.exit_code == 0
    assert "started" in result.stdout
    mock_start.assert_called_once_with(
        "issue-9-docker",
        yes=True,
        keep_ignored=False,
        prep=True,
        no_push=True,
    )


@patch.object(GitShortcuts, "reset", return_value=[])
def test_git_reset_with_yes(mock_reset: MagicMock, snapshot: MagicMock) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "reset", "--yes"])
    assert result.exit_code == 0
    assert "synced with remote" in result.stdout
    mock_reset.assert_called_once_with(
        yes=True,
        keep_ignored=False,
        main_only=True,
        branch_message=".",
        discard=False,
    )


@patch.object(GitShortcuts, "delete_all_local_branches", return_value=["a", "b"])
@patch.object(GitShortcuts, "local_branch_names", return_value=["a", "b"])
@patch.object(GitShortcuts, "reset", return_value=[])
def test_git_reset_all_local(
    mock_reset: MagicMock,
    _local: MagicMock,
    mock_delete: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(SNAPSHOT, return_value=snapshot):
        result = runner.invoke(app, ["git", "reset", "--yes", "--all-local"])
    assert result.exit_code == 0
    mock_reset.assert_called_once_with(
        yes=True,
        keep_ignored=False,
        main_only=True,
        branch_message=".",
        discard=False,
    )
    mock_delete.assert_called_once_with(yes=True)


"""Tests for cli git push (add + commit + push shortcut)."""


from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from src.cli import app
from src.commands.git import _interactive_allow_main, _push_plan
from src.services.git_shortcuts import GitShortcuts

runner = CliRunner()
GIT_SNAPSHOT_PATCH = "src.commands.git.git_worktree_snapshot"


@pytest.fixture
def snapshot() -> MagicMock:
    snap = MagicMock()
    snap.summary_lines.return_value = ["branch: feat-x", "dirty: true"]
    return snap


def test_push_plan_on_main_starts_branch_first() -> None:
    svc = MagicMock()
    svc.push_plan.return_value = GitPushPlan(
        source_branch="main",
        target_branch="wip-260611-001",
        remote="origin",
        dirty=True,
        message="wip",
        create_branch_first=True,
    )
    question, lines = _push_plan(svc, "wip", allow_main=False, use_branch=True)
    assert question.startswith("Start 'wip-")
    assert "commit, and push to origin?" in question
    assert any(line.startswith("target_branch: wip-") for line in lines)
    assert "from_branch: main" in lines


def test_push_plan_on_feature_branch() -> None:
    svc = MagicMock()
    svc.push_plan.return_value = GitPushPlan(
        source_branch="feat-x",
        target_branch="feat-x",
        remote="origin",
        dirty=False,
        message=".",
    )
    question, lines = _push_plan(svc, ".", allow_main=False)
    assert question == "Commit and push 'feat-x' to origin?"
    assert "branch: feat-x" in lines


def test_push_plan_without_origin_commits_locally() -> None:
    svc = MagicMock()
    svc.push_plan.return_value = GitPushPlan(
        source_branch="feat-x",
        target_branch="feat-x",
        remote=None,
        dirty=True,
        message="wip",
    )
    question, lines = _push_plan(svc, "wip", allow_main=False)
    assert question == "Commit local work on 'feat-x' without pushing?"
    assert "intent: git add -A → commit (no remote push)" in lines
    assert "remote: (none)" in lines


def test_push_plan_on_main_without_origin() -> None:
    svc = MagicMock()
    svc.push_plan.return_value = GitPushPlan(
        source_branch="main",
        target_branch="main",
        remote=None,
        dirty=True,
        message=".",
    )
    question, lines = _push_plan(svc, ".", allow_main=False)
    assert "main" in question
    assert "local-only commit on main" in "\n".join(lines)


def test_push_plan_warns_when_main_tracks_feature_upstream() -> None:
    svc = MagicMock()
    svc.push_plan.return_value = GitPushPlan(
        source_branch="main",
        target_branch="main",
        remote="origin",
        dirty=False,
        message=".",
        allow_main=True,
        warnings=("on main but upstream tracks 'feat-x'",),
    )
    _, lines = _push_plan(svc, ".", allow_main=True)
    assert "warning: on main but upstream tracks 'feat-x'" in lines


def test_push_plan_on_main_pushes_main_by_default() -> None:
    svc = MagicMock()
    svc.push_plan.return_value = GitPushPlan(
        source_branch="main",
        target_branch="main",
        remote="origin",
        dirty=True,
        message=".",
        allow_main=True,
    )
    question, lines = _push_plan(svc, ".", allow_main=True, use_branch=False)
    assert "main" in question
    assert "note: pushing directly on main" in lines


def test_interactive_allow_main_on_branch_flow(monkeypatch) -> None:
    svc = MagicMock()
    svc.push_plan.return_value = GitPushPlan(
        source_branch="main",
        target_branch="wip-001",
        remote="origin",
        dirty=False,
        message=".",
        create_branch_first=True,
    )
    monkeypatch.setattr("src.commands.git.sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("src.commands.git.typer.confirm", lambda *args, **kwargs: False)
    assert _interactive_allow_main(svc, allow_main=False, yes=False, use_branch=True) is False


@patch.object(GitShortcuts, "push")
def test_git_push_requires_yes(mock_push: MagicMock) -> None:
    result = runner.invoke(app, ["git", "push"])
    assert result.exit_code != 0
    mock_push.assert_not_called()


@patch.object(GitShortcuts, "is_dirty", return_value=True)
@patch.object(GitShortcuts, "remote_exists", return_value=True)
@patch.object(GitShortcuts, "current_branch", return_value="feat-x")
@patch.object(GitShortcuts, "push", return_value="feat-x")
def test_git_push_with_yes(
    mock_push: MagicMock,
    _branch: MagicMock,
    _remote: MagicMock,
    _dirty: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(GIT_SNAPSHOT_PATCH, return_value=snapshot):
        result = runner.invoke(app, ["git", "push", "--yes", "-m", "wip"])
    assert result.exit_code == 0
    assert "pushed" in result.stdout
    assert "intent: git add -A" in result.stdout
    assert "branch: feat-x" in result.stdout
    mock_push.assert_called_once_with(
        allow_main=True, message="wip", yes=True, use_branch=False
    )


@patch.object(GitShortcuts, "is_dirty", return_value=True)
@patch.object(GitShortcuts, "remote_exists", return_value=False)
@patch.object(GitShortcuts, "current_branch", return_value="feat-x")
@patch.object(
    GitShortcuts,
    "push",
    return_value=GitPushResult(branch="feat-x", pushed=False, remote=None, committed=True),
)
def test_git_push_without_origin_reports_local_commit(
    mock_push: MagicMock,
    _branch: MagicMock,
    _remote: MagicMock,
    _dirty: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(GIT_SNAPSHOT_PATCH, return_value=snapshot):
        result = runner.invoke(app, ["git", "push", "--yes", "-m", "wip"])
    assert result.exit_code == 0
    assert "no origin remote" in result.stdout
    assert "nothing pushed" in result.stdout
    mock_push.assert_called_once_with(
        allow_main=True, message="wip", yes=True, use_branch=False
    )


@patch.object(GitShortcuts, "current_branch", return_value="main")
@patch.object(GitShortcuts, "local_branch_names", return_value=[])
@patch.object(GitShortcuts, "is_dirty", return_value=True)
@patch.object(GitShortcuts, "remote_exists", return_value=True)
@patch.object(
    GitShortcuts,
    "push",
    return_value=GitPushResult(branch="main", pushed=True, remote="origin"),
)
def test_git_push_on_main_pushes_main_by_default(
    mock_push: MagicMock,
    _remote: MagicMock,
    _dirty: MagicMock,
    _branches: MagicMock,
    _current: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(GIT_SNAPSHOT_PATCH, return_value=snapshot):
        result = runner.invoke(app, ["git", "push", "--yes", "-m", "wip"])
    assert result.exit_code == 0
    assert "branch: main" in result.stdout
    assert "note: pushing directly on main" in result.stdout
    mock_push.assert_called_once_with(
        allow_main=True, message="wip", yes=True, use_branch=False
    )


@patch.object(GitShortcuts, "current_branch", return_value="main")
@patch.object(GitShortcuts, "local_branch_names", return_value=[])
@patch.object(GitShortcuts, "is_dirty", return_value=True)
@patch.object(GitShortcuts, "remote_exists", return_value=True)
@patch.object(GitShortcuts, "push", return_value="wip-260611-001")
def test_git_push_on_main_with_branch_flag_starts_first(
    mock_push: MagicMock,
    _remote: MagicMock,
    _dirty: MagicMock,
    _branches: MagicMock,
    _current: MagicMock,
    snapshot: MagicMock,
) -> None:
    with patch(GIT_SNAPSHOT_PATCH, return_value=snapshot):
        result = runner.invoke(app, ["git", "push", "--yes", "--branch", "-m", "wip"])
    assert result.exit_code == 0
    assert "target_branch: wip-" in result.stdout
    assert "from_branch: main" in result.stdout
    assert "intent: start 'wip-" in result.stdout
    mock_push.assert_called_once_with(
        allow_main=False, message="wip", yes=True, use_branch=True
    )


@patch.object(GitShortcuts, "push", return_value="feat-x")
def test_git_push_shows_write_gate(mock_push: MagicMock, snapshot: MagicMock) -> None:
    with patch(GIT_SNAPSHOT_PATCH, return_value=snapshot):
        result = runner.invoke(app, ["git", "push", "--yes"])
    assert result.exit_code == 0
    assert "--- cli write gate ---" in result.stdout
    assert "operation: push" in result.stdout
    mock_push.assert_called_once()


@patch.object(GitShortcuts, "is_detached_head", return_value=True)
def test_git_push_refuses_detached_head(_detached: MagicMock) -> None:
    result = runner.invoke(app, ["git", "push", "--yes"])
    assert result.exit_code != 0
    assert "detached HEAD" in result.stdout


@patch.object(
    GitShortcuts,
    "push",
    return_value=GitPushResult(
        branch="feat-x",
        pushed=True,
        remote="origin",
        warnings=("branch 'feat-x' is already merged into main",),
    ),
)
def test_git_push_json_format(mock_push: MagicMock, snapshot: MagicMock) -> None:
    with patch(GIT_SNAPSHOT_PATCH, return_value=snapshot):
        result = runner.invoke(app, ["git", "push", "--yes", "--format", "json"])
    assert result.exit_code == 0
    assert '"pushed": true' in result.stdout
    assert '"warnings"' in result.stdout
    assert "merged into main" in result.stdout
    mock_push.assert_called_once()


@patch.object(GitShortcuts, "current_branch", return_value="main")
@patch.object(
    GitShortcuts,
    "push",
    return_value=GitPushResult(branch="main", pushed=True, remote="origin"),
)
def test_cli_ship_pushes_main(mock_push: MagicMock, _branch: MagicMock, snapshot: MagicMock) -> None:
    with patch(GIT_SNAPSHOT_PATCH, return_value=snapshot):
        result = runner.invoke(app, ["ship", "--yes"])
    assert result.exit_code == 0
    assert "operation: ship" in result.stdout
    assert "pushed" in result.stdout
    mock_push.assert_called_once_with(
        allow_main=True, message=".", yes=True, use_branch=False
    )


@patch.object(GitShortcuts, "current_branch", return_value="feat-x")
def test_cli_ship_requires_main(_branch: MagicMock) -> None:
    result = runner.invoke(app, ["ship", "--yes"])
    assert result.exit_code != 0
    assert "checkout main" in result.stdout
