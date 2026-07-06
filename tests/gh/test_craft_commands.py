"""Unit tests for craft issue resolution commands."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()


@patch("src.commands.craft.review_epic")
@patch("src.commands.craft._svc")
def test_craft_epic_dry_run(mock_factory: MagicMock, mock_review_epic: MagicMock) -> None:
    svc = MagicMock()
    mock_factory.return_value = svc
    mock_review_epic.return_value = {"number": 1, "dry_run": True, "children": []}
    result = runner.invoke(app, ["craft", "epic", "--number", "1", "--dry-run"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["dry_run"] is True
    mock_review_epic.assert_called_once()
    assert mock_review_epic.call_args.kwargs["yes"] is False


@patch("src.commands.craft.review_epic")
@patch("src.commands.craft._svc")
def test_craft_epic_dry_run_value_false_writes(mock_factory: MagicMock, mock_review_epic: MagicMock) -> None:
    svc = MagicMock()
    svc.snapshot_summary.return_value = ["repo: owner/repo"]
    mock_factory.return_value = svc
    mock_review_epic.return_value = {"number": 1, "dry_run": False, "children": []}
    result = runner.invoke(app, ["craft", "epic", "--number", "1", "--dry-run-value", "false", "--yes"])
    assert result.exit_code == 0
    mock_review_epic.assert_called_once()
    assert mock_review_epic.call_args.kwargs["yes"] is True


@patch("src.commands.craft.pr_execution_plan")
@patch("src.commands.craft._svc")
def test_craft_pr_plan_uses_selected_issue(mock_factory: MagicMock, mock_plan: MagicMock) -> None:
    svc = MagicMock()
    mock_factory.return_value = svc
    mock_plan.return_value = {"issue": 2, "branch": "craft/2-child"}
    result = runner.invoke(app, ["craft", "pr-plan", "--number", "2"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["issue"] == 2
    mock_plan.assert_called_once_with(svc, 2, branch=None)


@patch("src.commands.craft.pr_execution_plan")
@patch("src.commands.craft._svc")
def test_craft_pr_plan_picks_next_child(mock_factory: MagicMock, mock_plan: MagicMock) -> None:
    svc = MagicMock()
    svc.backlog_next.return_value = {"number": 5, "title": "1.1 — Ready"}
    mock_factory.return_value = svc
    mock_plan.return_value = {"issue": 5, "branch": "craft/5-ready"}
    result = runner.invoke(app, ["craft", "pr-plan"])
    assert result.exit_code == 0
    mock_plan.assert_called_once_with(svc, 5, branch=None)


@patch("src.commands.craft.pr_execution_plan")
@patch("src.commands.craft._svc")
def test_craft_issue_to_pr_dry_run_picks_next_subissue(mock_factory: MagicMock, mock_plan: MagicMock) -> None:
    svc = MagicMock()
    svc.backlog_next.return_value = {"number": 8, "title": "1.1 — Ready"}
    mock_factory.return_value = svc
    mock_plan.return_value = {"issue": 8, "branch": "craft/8-ready"}
    result = runner.invoke(app, ["craft", "issue-to-pr", "--number", "", "--branch", "", "--dry-run", "true"])
    assert result.exit_code == 0
    mock_plan.assert_called_once_with(svc, 8, branch=None)
