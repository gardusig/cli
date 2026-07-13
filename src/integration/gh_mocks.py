"""Mock gh service/shortcut for unit and integration endpoint checks."""

from __future__ import annotations

from contextlib import AbstractContextManager, ExitStack, nullcontext
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    from src.integration.public_endpoints import EndpointCheck


def build_mock_gh_service() -> MagicMock:
    svc = MagicMock()
    svc.repo_display.return_value = "owner/repo"
    svc.snapshot_summary.return_value = ["repo: owner/repo"]
    svc.issue_list.return_value = [{"number": 1, "title": "1 — Epic"}]
    svc.issue_view.return_value = {"number": 1, "title": "One"}
    svc.issue_context.return_value = {
        "issue": {"number": 1, "title": "One"},
        "comments": [],
        "linked_issues": [],
        "labels": [],
    }
    svc.issue_search.return_value = [{"number": 2, "title": "Search hit"}]
    svc.issue_create.return_value = {"number": 42, "title": "Test", "url": "https://example/42"}
    svc.issue_edit.return_value = None
    svc.issue_reopen.return_value = {"number": 1, "state": "open"}
    svc.issue_status.return_value = {"open_issues": 1, "issues": [{"number": 1}]}
    svc.issue_delete.return_value = None
    svc.issue_comment.return_value = None
    svc.issue_batch.return_value = [{"number": 1, "action": "label"}]
    svc.branch_list.return_value = [{"name": "main", "sha": "abc", "protected": True}]
    svc.branch_view.return_value = {"name": "main", "sha": "abc"}
    svc.branch_delete.return_value = None
    svc.pr_list.return_value = [{"number": 5, "title": "PR"}]
    svc.pr_view.return_value = {"number": 5, "title": "PR"}
    svc.pr_diff_stat.return_value = " 1 file changed"
    svc.pr_status.return_value = {"open_prs": 1, "pull_requests": [{"number": 5}]}
    svc.pr_create.return_value = {"number": 6, "title": "New PR", "url": "https://example/6"}
    svc.pr_edit.return_value = None
    svc.pr_comment.return_value = None
    svc.pr_close.return_value = {"number": 5, "state": "closed"}
    svc.pr_reopen.return_value = {"number": 5, "state": "open"}
    svc.pr_checks.return_value = [{"name": "ci", "state": "SUCCESS"}]
    svc.pr_review.return_value = {"id": 1}
    svc.pr_ready.return_value = {"number": 5, "isDraft": False}
    return svc


def build_mock_gh_pr_shortcut(svc: MagicMock | None = None) -> MagicMock:
    shortcut = MagicMock()
    shortcut.gh = svc or build_mock_gh_service()
    shortcut.find_open_pr_for_branch.return_value = {"number": 7, "title": "Feature"}
    shortcut.upsert_branch_pr.return_value = {"number": 8, "title": "Upsert", "url": "https://example/8"}
    return shortcut


def _gh_subcommand_tokens(args: tuple[str, ...]) -> tuple[str, ...]:
    if not args or args[0] != "gh":
        return ()
    tokens = list(args[1:])
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if not token.startswith("--"):
            break
        if token in ("--format", "--repo", "--transport") and index + 1 < len(tokens):
            index += 2
            continue
        index += 1
    return tuple(tokens[index:])


def gh_endpoint_needs_mock(check: EndpointCheck) -> bool:
    if not check.args or check.args[0] != "gh":
        return False
    if check.label == "gh help":
        return False
    sub = _gh_subcommand_tokens(check.args)
    if not sub:
        return False
    if sub[0] == "policy":
        return False
    if sub[0] == "ruleset":
        return False
    if sub[:2] == ("issue", "close"):
        return False
    if sub[:2] == ("pr", "merge"):
        return False
    return True


def gh_endpoint_patches(check: EndpointCheck) -> AbstractContextManager[object]:
    if not gh_endpoint_needs_mock(check):
        return nullcontext()
    svc = build_mock_gh_service()
    shortcut = build_mock_gh_pr_shortcut(svc)
    stack = ExitStack()
    stack.enter_context(patch("src.commands.gh._svc", return_value=svc))
    stack.enter_context(patch("src.commands.gh._pr_shortcut", return_value=shortcut))
    return stack
