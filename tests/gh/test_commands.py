"""Unit tests for cli gh commands and services."""

from __future__ import annotations

from tests.constants import ROOT

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from src.cli import app
from src.services.gh_sequence import SequenceKey, sort_issues_by_sequence
from src.services.project_service import ProjectRef

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


@patch("src.commands.gh._svc")
def test_backlog_next(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    mock_svc.backlog_next.return_value = {"number": 5, "title": "1.1 — Child", "sequence": "1.1 —"}
    result = runner.invoke(app, ["gh", "--format", "json", "backlog", "next"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["number"] == 5


@patch("src.commands.gh._svc")
def test_label_sync_with_yes(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    mock_svc.label_sync.return_value = {"created": ["epic:test"], "deleted": []}
    result = runner.invoke(
        app,
        ["gh", "label", "sync", "--manifest", "labels.yaml", "--yes"],
    )
    assert result.exit_code == 0


def test_gh_help() -> None:
    result = runner.invoke(app, ["gh", "--help"])
    assert result.exit_code == 0
    assert "issue" in result.output


@patch("src.commands.gh._svc")
def test_repo_view_json(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    mock_svc.repo_view.return_value = {"nameWithOwner": "owner/repo", "owner": {"login": "owner"}}
    result = runner.invoke(
        app,
        ["gh", "--format", "json", "repo", "view", "--json-fields", "nameWithOwner,owner"],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["nameWithOwner"] == "owner/repo"
    mock_svc.repo_view.assert_called_once_with(fields="nameWithOwner,owner")


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


@patch("src.commands.gh._svc")
def test_repo_list_json(mock_factory: MagicMock, mock_svc: MagicMock) -> None:
    mock_factory.return_value = mock_svc
    mock_svc.repo_list.return_value = [{"name": "python-cli", "description": "CLI"}]
    result = runner.invoke(app, ["gh", "--format", "json", "repo", "list"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data[0]["name"] == "python-cli"
    mock_svc.repo_list.assert_called_once()


class FakeProjectService:
    def ref(self, *, owner=None, number=None, project_id=None):  # noqa: ANN001
        return ProjectRef(owner=owner or "owner", number=number or 1, project_id=project_id or "PVT_1")

    def snapshot_summary(self, ref=None):  # noqa: ANN001
        ref = ref or self.ref()
        return [f"owner: {ref.owner}", f"project: {ref.number}"]

    def project_list(self, *, owner: str, limit: int = 30):
        return [{"number": 1, "title": "Roadmap", "owner": owner, "limit": limit}]

    def project_view(self, number: int, *, owner: str):
        return {"number": number, "owner": owner}

    def project_node(self, ref: ProjectRef):
        return {"id": ref.project_id, "number": ref.number, "owner": ref.owner, "source": "graphql"}

    def project_create(self, *, owner: str, title: str):
        return {"number": 2, "owner": owner, "title": title}

    def project_edit(self, number: int, *, owner: str, title=None, readme=None, visibility=None):  # noqa: ANN001
        return {"number": number, "owner": owner, "title": title, "visibility": visibility}

    def project_delete(self, number: int, *, owner: str):
        return {"number": number, "owner": owner, "deleted": True}

    def item_list(self, ref: ProjectRef, *, limit: int = 100):
        return [{"id": "ITEM_1", "project": ref.number, "limit": limit}]

    def item_view(self, item_id: str, ref: ProjectRef):
        return {"id": item_id, "project": ref.number}

    def item_add_issue(self, issue: int, ref: ProjectRef):
        return {"id": "ITEM_1", "issue": issue, "project": ref.number}

    def item_status(self, ref: ProjectRef, *, item_id: str, status: str):
        return {"id": item_id, "status": status, "project": ref.number}

    def find_item(self, ref: ProjectRef, *, item_id=None, issue=None, pr=None):  # noqa: ANN001
        return {"id": item_id or "ITEM_1", "issue": issue, "pr": pr, "project": ref.number}

    def item_set(self, ref: ProjectRef, *, item_id: str, field: str, value: str, value_kind: str):
        return {"id": item_id, "field": field, "value": value, "kind": value_kind}

    def item_delete(self, ref: ProjectRef, *, item_id: str):
        return {"id": item_id, "deleted": True}


@patch("src.commands.gh._project_svc")
def test_gh_project_crud_commands(mock_factory: MagicMock) -> None:
    mock_factory.return_value = FakeProjectService()
    list_result = runner.invoke(app, ["gh", "project", "list", "--owner", "owner"])
    assert list_result.exit_code == 0
    assert json.loads(list_result.stdout)[0]["number"] == 1

    create_result = runner.invoke(app, ["gh", "project", "create", "--owner", "owner", "--title", "Roadmap", "--yes"])
    assert create_result.exit_code == 0
    assert json.loads(create_result.stdout[create_result.stdout.index("{") :])["title"] == "Roadmap"

    edit_result = runner.invoke(app, ["gh", "project", "edit", "1", "--owner", "owner", "--title", "Updated", "--yes"])
    assert edit_result.exit_code == 0
    assert json.loads(edit_result.stdout[edit_result.stdout.index("{") :])["title"] == "Updated"

    delete_result = runner.invoke(app, ["gh", "project", "delete", "1", "--owner", "owner", "--yes"])
    assert delete_result.exit_code == 0
    assert json.loads(delete_result.stdout[delete_result.stdout.index("{") :])["deleted"] is True


@patch("src.commands.gh._project_svc")
def test_gh_project_view_uses_graphql_for_api_transport(mock_factory: MagicMock) -> None:
    mock_factory.return_value = FakeProjectService()
    result = runner.invoke(app, ["gh", "--transport", "api", "project", "view", "1", "--owner", "owner"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["source"] == "graphql"


@patch("src.commands.gh._project_svc")
def test_gh_project_item_crud_commands(mock_factory: MagicMock) -> None:
    mock_factory.return_value = FakeProjectService()
    add_result = runner.invoke(
        app,
        ["gh", "project", "item", "add", "--project", "1", "--owner", "owner", "--issue", "42", "--yes"],
    )
    assert add_result.exit_code == 0
    assert json.loads(add_result.stdout[add_result.stdout.index("{") :])["issue"] == 42

    edit_result = runner.invoke(
        app,
        [
            "gh",
            "project",
            "item",
            "edit",
            "--project",
            "1",
            "--owner",
            "owner",
            "--id",
            "ITEM_1",
            "--field",
            "Status",
            "--value",
            "Done",
            "--kind",
            "single-select",
            "--yes",
        ],
    )
    assert edit_result.exit_code == 0
    assert json.loads(edit_result.stdout[edit_result.stdout.index("{") :])["value"] == "Done"

    delete_result = runner.invoke(
        app,
        ["gh", "project", "item", "delete", "--project", "1", "--owner", "owner", "--id", "ITEM_1", "--yes"],
    )
    assert delete_result.exit_code == 0
    assert json.loads(delete_result.stdout[delete_result.stdout.index("{") :])["deleted"] is True


@patch("src.services.gh_repo_readme.sync_profile_readme")
def test_repo_readme_sync_dry_run(mock_sync: MagicMock, tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("before\n", encoding="utf-8")
    mock_sync.return_value = ("after\n", [{"name": "cli"}])
    result = runner.invoke(
        app,
        ["gh", "repo", "readme-sync", "--readme", str(readme), "--dry-run"],
    )
    assert result.exit_code == 0
    assert "after" in result.stdout
    assert readme.read_text(encoding="utf-8") == "before\n"
