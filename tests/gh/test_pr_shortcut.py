from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from src.cli import app
from src.services.gh_pr_shortcut import GhPrShortcut, PrShortcutPlan
from src.services.git_shortcuts import GitPushPlan, GitPushResult

runner = CliRunner()


def _push_plan(
    *,
    branch: str = "feat-x",
    dirty: bool = False,
    remote: str | None = "origin",
    create_branch_first: bool = False,
) -> GitPushPlan:
    return GitPushPlan(
        source_branch="main" if create_branch_first else branch,
        target_branch=branch,
        remote=remote,
        dirty=dirty,
        message=".",
        create_branch_first=create_branch_first,
    )


def test_pr_shortcut_pushes_dirty_branch_before_create() -> None:
    gh = MagicMock()
    gh.pr_create.return_value = {"url": "https://github.com/o/r/pull/7", "number": 7, "title": "."}
    git = MagicMock()
    git.top = "/repo"
    git.push_plan.return_value = _push_plan(dirty=True)
    git.push.return_value = GitPushResult(branch="feat-x", pushed=True, remote="origin", committed=True)
    shortcut = GhPrShortcut(gh=gh, git=git, repo_root=Path("/repo"))

    plan = shortcut.plan()
    payload = shortcut.create(plan, yes=True)

    assert plan.needs_push is True
    assert payload["pushed"] is True
    assert payload["branch"] == "feat-x"
    git.push.assert_called_once_with(allow_main=False, message=".", yes=True)
    gh.pr_create.assert_called_once_with(title=".", body="")


def test_pr_shortcut_skips_push_when_branch_is_published() -> None:
    gh = MagicMock()
    gh.pr_create.return_value = {"url": "https://github.com/o/r/pull/8", "number": 8, "title": "."}
    git = MagicMock()
    git.top = "/repo"
    git.push_plan.return_value = _push_plan(dirty=False)
    git.rev_parse.return_value = "abc123"
    git.commit_on_remote_branch.return_value = True
    shortcut = GhPrShortcut(gh=gh, git=git, repo_root=Path("/repo"))

    plan = shortcut.plan()
    payload = shortcut.create(plan, yes=True)

    assert plan.needs_push is False
    assert payload["pushed"] is False
    git.push.assert_not_called()


def test_pr_shortcut_no_push_refuses_unpublished_branch() -> None:
    gh = MagicMock()
    git = MagicMock()
    git.top = "/repo"
    git.push_plan.return_value = _push_plan(dirty=True)
    shortcut = GhPrShortcut(gh=gh, git=git, repo_root=Path("/repo"))

    plan = shortcut.plan(no_push=True)

    with pytest.raises(RuntimeError, match="not ready"):
        shortcut.create(plan, yes=True)
    git.push.assert_not_called()
    gh.pr_create.assert_not_called()


def test_pr_shortcut_local_template_resolution(tmp_path: Path) -> None:
    template_dir = tmp_path / ".github" / "PULL_REQUEST_TEMPLATE"
    template_dir.mkdir(parents=True)
    (template_dir / "bugfix.md").write_text("Bugfix body\n", encoding="utf-8")
    gh = MagicMock()
    gh.repo_view.side_effect = RuntimeError("offline")
    git = MagicMock()
    git.top = str(tmp_path)
    git.push_plan.return_value = _push_plan(dirty=False)
    git.rev_parse.return_value = "abc123"
    git.commit_on_remote_branch.return_value = True
    shortcut = GhPrShortcut(gh=gh, git=git, repo_root=tmp_path)

    body, source = shortcut.resolve_body(body="", template="bugfix")

    assert body == "Bugfix body\n"
    assert source == "local:.github/PULL_REQUEST_TEMPLATE/bugfix.md"


def test_pr_shortcut_remote_template_resolution() -> None:
    gh = MagicMock()
    gh.repo_view.return_value = {
        "pullRequestTemplates": [
            {"name": "feature.md", "body": "Feature body\n"},
            {"name": "bugfix.md", "body": "Bugfix body\n"},
        ]
    }
    git = MagicMock()
    git.top = "/repo"
    shortcut = GhPrShortcut(gh=gh, git=git, repo_root=Path("/repo"))

    body, source = shortcut.resolve_body(body="", template="feature")

    assert body == "Feature body\n"
    assert source == "remote:feature.md"
    gh.repo_view.assert_called_once_with(fields="pullRequestTemplates")


class FakeShortcut:
    def __init__(self) -> None:
        self.gh = MagicMock()
        self.gh.snapshot_summary.return_value = ["repo: owner/repo"]
        self.plan_value = PrShortcutPlan(
            title=".",
            body="",
            body_source="empty",
            template=None,
            no_push=False,
            allow_main=False,
            push_plan=_push_plan(dirty=True),
            needs_push=True,
            branch="feat-x",
        )

    def plan(self, **kwargs):
        self.kwargs = kwargs
        return self.plan_value

    def create(self, plan, *, yes: bool):
        assert yes is True
        assert plan is self.plan_value
        return {
            "url": "https://github.com/o/r/pull/9",
            "number": 9,
            "title": ".",
            "pushed": True,
            "branch": "feat-x",
        }


def test_cli_gh_pr_shortcut_default(monkeypatch) -> None:
    from src.commands import gh

    fake = FakeShortcut()
    monkeypatch.setattr(gh, "_pr_shortcut", lambda repo=None: fake)

    result = runner.invoke(app, ["gh", "pr", "--yes"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert payload["pushed"] is True
    assert payload["branch"] == "feat-x"
    assert fake.kwargs["title"] == "."


def test_cli_gh_pr_subcommands_still_work(monkeypatch) -> None:
    from src.commands import gh

    svc = MagicMock()
    svc.pr_list.return_value = [{"number": 1, "title": "PR"}]
    monkeypatch.setattr(gh, "_svc", lambda repo=None: svc)

    result = runner.invoke(app, ["gh", "--format", "json", "pr", "list"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)[0]["number"] == 1
    svc.pr_list.assert_called_once_with(state="open", limit=30, head=None, base=None)
