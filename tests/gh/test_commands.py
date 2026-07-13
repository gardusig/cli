"""Unit tests for cli gh commands and services."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from src.cli import app
from src.services.gh_sequence import SequenceKey, sort_issues_by_sequence

runner = CliRunner()


@pytest.fixture
def mock_svc() -> MagicMock:
    svc = MagicMock()
    svc.repo_display.return_value = "owner/repo"
    svc.snapshot_summary.return_value = ["repo: owner/repo"]
    return svc


def test_sequence_key_from_title() -> None:
    assert SequenceKey.from_title("1 — Epic foo") == SequenceKey(1, None)
    assert SequenceKey.from_title("1.2 — Child bar") == SequenceKey(1, 2)
    assert SequenceKey.from_title("no prefix") is None


def test_sort_issues_by_sequence() -> None:
    issues = [
        {"number": 3, "title": "2 — Second"},
        {"number": 1, "title": "1.2 — Child"},
        {"number": 2, "title": "1 — Epic"},
    ]
    ordered = sort_issues_by_sequence(issues)
    assert [i["number"] for i in ordered] == [2, 1, 3]


@patch("src.commands.gh._svc")
def test_issue_list_json(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    mock_svc.issue_list.return_value = [{"number": 1, "title": "1 — Epic"}]
    result = runner.invoke(app, ["gh", "--format", "json", "issue", "list"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data[0]["number"] == 1


@patch("src.commands.gh._svc")
def test_issue_context_json(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    mock_svc.issue_context.return_value = {
        "issue": {"number": 2, "title": "1.1 — Child"},
        "comments": [{"body": "note"}],
        "epic": {"slug": "epic:wf", "parent": {"number": 1, "title": "Epic"}},
        "siblings": [{"number": 3, "title": "1.2 — Other"}],
        "linked_issues": [],
        "labels": ["epic:wf"],
    }
    result = runner.invoke(app, ["gh", "--format", "json", "issue", "context", "2"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["epic"]["parent"]["number"] == 1
    mock_svc.issue_context.assert_called_once_with(2)


@patch("src.commands.gh._svc")
def test_issue_create_requires_yes_in_non_tty(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    result = runner.invoke(
        app,
        ["gh", "issue", "create", "--title", "Test"],
    )
    assert result.exit_code != 0
    assert "non-interactive" in result.output.lower() or result.exit_code == 1


@patch("src.commands.gh._svc")
def test_issue_create_with_yes(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    mock_svc.issue_create.return_value = {"number": 42, "title": "Test", "url": "https://x/42"}
    result = runner.invoke(
        app,
        ["gh", "issue", "create", "--title", "Test", "--yes"],
    )
    assert result.exit_code == 0
    mock_svc.issue_create.assert_called_once()


def test_issue_close_blocked() -> None:
    result = runner.invoke(app, ["gh", "issue", "close", "42", "--yes"])
    assert result.exit_code != 0
    assert "issue close blocked" in result.output


@patch("src.commands.gh._svc")
def test_issue_reopen_and_status_commands(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    mock_svc.issue_reopen.return_value = {"number": 42, "state": "open"}
    reopen = runner.invoke(app, ["gh", "issue", "reopen", "42", "--yes"])
    assert reopen.exit_code == 0
    assert json.loads(reopen.stdout[reopen.stdout.index("{") :])["state"] == "open"

    mock_svc.issue_status.return_value = {"open_issues": 2, "issues": [{"number": 1}]}
    status = runner.invoke(app, ["gh", "issue", "status"])
    assert status.exit_code == 0
    assert json.loads(status.stdout)["open_issues"] == 2


def test_gh_help() -> None:
    result = runner.invoke(app, ["gh", "--help"])
    assert result.exit_code == 0
    assert "issue" in result.output
    assert "branch" in result.output
    assert "pr" in result.output


@patch("src.commands.gh._svc")
def test_branch_list_json(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    mock_svc.branch_list.return_value = [{"name": "main", "sha": "abc", "protected": True}]
    result = runner.invoke(app, ["gh", "--format", "json", "branch", "list"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data[0]["name"] == "main"


@patch("src.commands.gh._pr_shortcut")
def test_branch_pr_json(mock_factory: MagicMock) -> None:
    shortcut = MagicMock()
    shortcut.find_open_pr_for_branch.return_value = {"number": 7, "title": "Feature"}
    mock_factory.return_value = shortcut
    result = runner.invoke(app, ["gh", "--format", "json", "branch", "pr", "feature"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["pull_request"]["number"] == 7


@patch("src.commands.gh._svc")
def test_branch_delete_requires_yes(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    result = runner.invoke(app, ["gh", "branch", "delete", "wip"])
    assert result.exit_code != 0


@patch("src.commands.gh._svc")
def test_issue_view_table_format(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    mock_svc.issue_view.return_value = {"number": 9, "title": "Nine"}
    result = runner.invoke(app, ["gh", "--format", "table", "issue", "view", "9"])
    assert result.exit_code == 0
    assert "Nine" in result.stdout


@patch("src.commands.gh._svc")
def test_pr_list_head_base_filters(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    mock_svc.pr_list.return_value = [{"number": 1, "title": "PR"}]
    result = runner.invoke(
        app,
        ["gh", "--format", "json", "pr", "list", "--head", "feature", "--base", "main"],
    )
    assert result.exit_code == 0
    mock_svc.pr_list.assert_called_once_with(state="open", limit=30, head="feature", base="main")


@patch("src.commands.gh._svc")
def test_pr_workflow_commands(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    mock_svc.pr_reopen.return_value = {"number": 5, "state": "open"}
    reopen = runner.invoke(app, ["gh", "pr", "reopen", "5", "--yes"])
    assert reopen.exit_code == 0
    assert json.loads(reopen.stdout[reopen.stdout.index("{") :])["state"] == "open"

    comment = runner.invoke(app, ["gh", "pr", "comment", "5", "--body", "note", "--yes"])
    assert comment.exit_code == 0
    mock_svc.pr_comment.assert_called_with(5, body="note")

    mock_svc.pr_checks.return_value = [{"name": "ci", "state": "SUCCESS"}]
    checks = runner.invoke(app, ["gh", "pr", "checks", "5"])
    assert checks.exit_code == 0
    assert json.loads(checks.stdout)[0]["name"] == "ci"

    mock_svc.pr_review.return_value = {"id": 1}
    review = runner.invoke(app, ["gh", "pr", "review", "5", "--approve", "--body", "ok", "--yes"])
    assert review.exit_code == 0
    mock_svc.pr_review.assert_called_with(
        5,
        approve=True,
        request_changes=False,
        comment=False,
        body="ok",
    )

    mock_svc.pr_ready.return_value = {"number": 5, "isDraft": False}
    ready = runner.invoke(app, ["gh", "pr", "ready", "5", "--yes"])
    assert ready.exit_code == 0
    assert json.loads(ready.stdout[ready.stdout.index("{") :])["isDraft"] is False


@patch("src.commands.gh._svc")
def test_pr_status_command(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    mock_svc.pr_status.return_value = {"open_prs": 1, "pull_requests": [{"number": 5}]}
    result = runner.invoke(app, ["gh", "pr", "status"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["open_prs"] == 1
