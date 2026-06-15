"""Unit tests for GhService (mocked gh provider)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from shuttle.services.gh_service import GhService


@pytest.fixture
def provider() -> MagicMock:
    return MagicMock()


@pytest.fixture
def svc(provider: MagicMock) -> GhService:
    service = GhService(repo="owner/repo")
    service.provider = provider
    provider.repo = "owner/repo"
    return service


def test_repo_display_uses_explicit_repo(svc: GhService) -> None:
    assert svc.repo_display() == "owner/repo"


def test_repo_display_falls_back_to_default_repo(provider: MagicMock) -> None:
    service = GhService()
    service.provider = provider
    provider.repo = None
    provider.default_repo.return_value = "acme/widget"
    assert service.repo_display() == "acme/widget"


def test_issue_list_builds_args(svc: GhService, provider: MagicMock) -> None:
    provider.run_json.return_value = [{"number": 1}]
    rows = svc.issue_list(state="closed", label=["bug"], limit=5)
    assert rows == [{"number": 1}]
    args = provider.run_json.call_args[0][0]
    assert args[:4] == ["issue", "list", "--state", "closed"]
    assert "--limit" in args and "5" in args
    assert "--label" in args and "bug" in args


def test_issue_view_includes_comments_flag(svc: GhService, provider: MagicMock) -> None:
    provider.run_json.return_value = {"number": 2}
    svc.issue_view(2, comments=True)
    args = provider.run_json.call_args[0][0]
    assert args[0:3] == ["issue", "view", "2"]
    assert "--comments" in args


def test_issue_search(svc: GhService, provider: MagicMock) -> None:
    provider.run_json.return_value = []
    svc.issue_search("is:open", limit=10)
    args = provider.run_json.call_args[0][0]
    assert args[0:3] == ["search", "issues", "is:open"]


def test_issue_create_parses_number_from_url(svc: GhService, provider: MagicMock) -> None:
    provider.run.return_value = "https://github.com/owner/repo/issues/99"
    created = svc.issue_create(title="Hello", body="Body", labels=["a", "b"])
    assert created["number"] == 99
    provider.run.assert_called_once()
    args = provider.run.call_args[0][0]
    assert "create" in args
    assert "--label" in args


def test_issue_edit_and_close(svc: GhService, provider: MagicMock) -> None:
    svc.issue_edit(3, title="New", add_labels=["x"], remove_labels=["y"])
    svc.issue_close(3, comment="done")
    assert provider.run.call_count == 2


def test_issue_delete_and_comment(svc: GhService, provider: MagicMock) -> None:
    svc.issue_delete(4)
    svc.issue_comment(4, body="note")
    assert provider.run.call_count == 2


def test_issue_batch_create_and_edit(tmp_path: Path, svc: GhService, provider: MagicMock) -> None:
    batch = tmp_path / "batch.yaml"
    batch.write_text(
        yaml.safe_dump(
            {
                "operations": [
                    {"action": "create", "title": "One", "body": "b"},
                    {"action": "edit", "number": 2, "title": "Two"},
                    {"action": "close", "number": 3, "comment": "bye"},
                ]
            }
        ),
        encoding="utf-8",
    )
    provider.run.return_value = "https://github.com/o/r/issues/10"
    results = svc.issue_batch(batch)
    assert len(results) == 3


def test_issue_batch_unknown_action(tmp_path: Path, svc: GhService) -> None:
    batch = tmp_path / "bad.yaml"
    batch.write_text(yaml.safe_dump({"operations": [{"action": "nope"}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="Unknown batch action"):
        svc.issue_batch(batch)


def test_label_list_create_delete(svc: GhService, provider: MagicMock) -> None:
    provider.run_json.return_value = [{"name": "bug"}]
    assert svc.label_list()[0]["name"] == "bug"
    svc.label_create("feat", color="ff0000", description="feature")
    svc.label_delete("feat")
    assert provider.run.call_count == 2


def test_label_sync_creates_missing(svc: GhService, provider: MagicMock, tmp_path: Path) -> None:
    manifest = tmp_path / "labels.yaml"
    manifest.write_text(
        yaml.safe_dump({"labels": [{"name": "epic:test", "color": "abcdef"}]}),
        encoding="utf-8",
    )
    provider.run_json.return_value = []
    result = svc.label_sync(manifest)
    assert result["created"] == ["epic:test"]
    provider.run.assert_called()


def test_label_sync_prune_orphans(svc: GhService, provider: MagicMock, tmp_path: Path) -> None:
    manifest = tmp_path / "labels.yaml"
    manifest.write_text(yaml.safe_dump({"labels": []}), encoding="utf-8")
    provider.run_json.return_value = [{"name": "orphan"}]
    result = svc.label_sync(manifest, prune_orphans=True)
    assert result["deleted"] == ["orphan"]


def test_pr_list_view_diff_create(svc: GhService, provider: MagicMock) -> None:
    provider.run_json.return_value = [{"number": 1}]
    assert svc.pr_list(head="feat", base="main")
    provider.run_json.return_value = {"number": 1}
    svc.pr_view(1)
    provider.run.return_value = "stat"
    assert svc.pr_diff_stat(1) == "stat"
    provider.run.return_value = "https://github.com/o/r/pull/5"
    created = svc.pr_create(title="PR", body="b", base="main", head="feat")
    assert created["number"] == 5
    svc.pr_edit(5, title="Renamed")
    svc.pr_close(5)
    svc.pr_merge(5, delete_branch=True)


def test_repo_view(svc: GhService, provider: MagicMock) -> None:
    provider.run_json.return_value = {"nameWithOwner": "o/r"}
    assert svc.repo_view()["nameWithOwner"] == "o/r"


def test_backlog_tree_groups_epics(svc: GhService, provider: MagicMock) -> None:
    provider.run_json.return_value = [
        {"number": 1, "title": "1 — Epic", "labels": ["issue-type:epic"]},
        {"number": 2, "title": "1.1 — Child", "labels": ["issue-type:child", "epic:foo"]},
    ]
    tree = svc.backlog_tree()
    assert tree["repo"] == "owner/repo"
    assert tree["issues"]


def test_backlog_next_prefers_child_label(svc: GhService, provider: MagicMock) -> None:
    provider.run_json.return_value = [
        {"number": 2, "title": "1.2 — Child", "labels": [{"name": "issue-type:child"}]},
        {"number": 1, "title": "1.1 — Child", "labels": [{"name": "issue-type:child"}]},
    ]
    nxt = svc.backlog_next()
    assert nxt is not None
    assert nxt["number"] == 1


def test_backlog_resequence(tmp_path: Path, svc: GhService, provider: MagicMock) -> None:
    plan = tmp_path / "plan.yaml"
    plan.write_text(
        yaml.safe_dump({"renames": [{"number": 7, "title": "2 — Renamed"}]}),
        encoding="utf-8",
    )
    rows = svc.backlog_resequence(plan)
    assert rows == [{"number": 7, "title": "2 — Renamed"}]


def test_snapshot_summary(svc: GhService) -> None:
    assert svc.snapshot_summary() == ["repo: owner/repo"]
