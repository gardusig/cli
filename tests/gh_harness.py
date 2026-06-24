"""GitHub gh CLI mocks for integration tests."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from cli.utils.process import GhCommandError


def _load_json(path: Path, default: object) -> object:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


@contextmanager
def patch_gh_all(workspace: Path) -> Iterator[None]:
    """Mock GhProvider reads/writes with fixture JSON (happy-path responses)."""
    issues_path = workspace / "issues.json"
    prs_path = workspace / "prs.json"
    issues = _load_json(issues_path, [])
    child_issue = {
        "number": 5,
        "title": "1.1 — Child task",
        "labels": [{"name": "issue-type:child"}],
    }
    issues_with_child = [*issues, child_issue]
    prs = _load_json(prs_path, [])
    labels = [{"name": "test", "color": "ededed", "description": ""}]

    def _run_json(self, args: list[str]):
        cmd = list(args)
        if cmd[:2] == ["issue", "list"]:
            return issues_with_child
        if cmd[:2] == ["issue", "view"]:
            number = int(cmd[2])
            for row in issues:
                if row.get("number") == number:
                    return {
                        **row,
                        "body": "fixture body",
                        "author": {"login": "test"},
                        "createdAt": "2026-01-01",
                        "updatedAt": "2026-01-02",
                    }
            raise RuntimeError(f"issue {number} not in fixture")
        if cmd[:2] == ["search", "issues"]:
            return issues_with_child
        if cmd[:2] == ["label", "list"]:
            return labels
        if cmd[:2] == ["pr", "list"]:
            return prs
        if cmd[:2] == ["pr", "view"]:
            number = int(cmd[2])
            for row in prs:
                if row.get("number") == number:
                    return {**row, "body": "fixture pr body", "commits": [], "files": []}
            raise RuntimeError(f"pr {number} not in fixture")
        if cmd[:3] == ["repo", "view", "--json"]:
            return {
                "nameWithOwner": "example/repo",
                "owner": {"login": "example"},
                "issueTemplates": [],
                "pullRequestTemplates": [],
            }
        raise RuntimeError(f"unmocked gh run_json: {cmd}")

    def _run(self, args: list[str], *, check: bool = True) -> str:
        cmd = list(args)
        if cmd[:2] == ["issue", "create"]:
            return "https://github.com/example/repo/issues/99"
        if cmd[:2] == ["pr", "create"]:
            return "https://github.com/example/repo/pull/8"
        if cmd[:2] == ["pr", "diff"]:
            return "1 file changed, 10 insertions(+)"
        if cmd[0] == "issue" and cmd[1] in {
            "edit",
            "close",
            "delete",
            "comment",
            "edit",
        }:
            return ""
        if cmd[0] == "label" and cmd[1] in {"create", "delete"}:
            return ""
        if cmd[0] == "pr" and cmd[1] in {"edit", "close", "merge"}:
            return ""
        if cmd[:2] == ["issue", "batch"]:
            return ""
        raise RuntimeError(f"unmocked gh run: {cmd}")

    with (
        patch("cli.providers.gh.GhProvider.run_json", _run_json),
        patch("cli.providers.gh.GhProvider.run", _run),
    ):
        yield


def patch_gh_json(fixture_path: Path):
    """Legacy narrow patch (issue list/view only). Prefer patch_gh_all."""
    return patch_gh_all(fixture_path.parent)


@contextmanager
def patch_run_gh(
    *,
    handler=None,
    side_effect: Exception | None = None,
) -> Iterator[None]:
    """Patch low-level run_gh so ExternalClient retry logic is exercised."""

    def _run_gh(args, *, cwd=None, check=True):
        if side_effect is not None:
            raise side_effect
        if handler is not None:
            return handler(list(args), cwd=cwd, check=check)
        raise RuntimeError("patch_run_gh: provide handler or side_effect")

    with patch("cli.providers.gh.run_gh", _run_gh):
        yield


def gh_auth_error() -> GhCommandError:
    return GhCommandError(
        ["gh", "issue", "list"],
        1,
        "HTTP 401: not logged in to any hosts",
    )


def gh_transient_error() -> GhCommandError:
    return GhCommandError(
        ["gh", "issue", "list"],
        1,
        "HTTP 503: service unavailable",
    )
