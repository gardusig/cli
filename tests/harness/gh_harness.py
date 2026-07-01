"""GitHub gh CLI mocks for integration tests."""

from __future__ import annotations

import copy
import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import patch

from src.utils.process import GhCommandError


def _load_json(path: Path, default: object) -> object:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


@dataclass
class StatefulGhStore:
    """In-memory gh state for workflow integration tests."""

    issues: list[dict]
    prs: list[dict]
    labels: list[dict]
    next_issue_number: int = 100
    pr_create_calls: list[list[str]] = field(default_factory=list)
    issue_bodies: dict[int, str] = field(default_factory=dict)
    issue_comments: dict[int, list[dict]] = field(default_factory=dict)

    @classmethod
    def from_workspace(cls, workspace: Path) -> StatefulGhStore:
        issues = copy.deepcopy(_load_json(workspace / "issues.json", []))
        if not isinstance(issues, list):
            issues = []
        prs = copy.deepcopy(_load_json(workspace / "prs.json", []))
        if not isinstance(prs, list):
            prs = []
        labels = copy.deepcopy(_load_json(workspace / "labels.json", []))
        if not labels:
            labels = [{"name": "test", "color": "ededed", "description": ""}]
        max_num = max((int(i.get("number", 0)) for i in issues), default=0)
        store = cls(issues=issues, prs=prs, labels=labels, next_issue_number=max_num + 1)
        for issue in issues:
            num = int(issue["number"])
            store.issue_bodies[num] = str(issue.get("body", "fixture body"))
            store.issue_comments[num] = [
                {
                    "author": {"login": "reviewer"},
                    "body": f"Comment on #{num}",
                    "createdAt": "2026-01-02",
                }
            ]
        return store

    def _find_issue(self, number: int) -> dict | None:
        for row in self.issues:
            if int(row.get("number", -1)) == number:
                return row
        return None

    def issue_create(
        self,
        *,
        title: str,
        body: str | None = None,
        labels: list[str] | None = None,
    ) -> tuple[str, int]:
        number = self.next_issue_number
        self.next_issue_number += 1
        label_objs = [{"name": lb} for lb in (labels or [])]
        text = body or ""
        issue = {
            "number": number,
            "title": title,
            "state": "OPEN",
            "labels": label_objs,
            "url": f"https://github.com/example/repo/issues/{number}",
            "body": text,
        }
        self.issues.append(issue)
        self.issue_bodies[number] = text
        self.issue_comments[number] = []
        return f"https://github.com/example/repo/issues/{number}", number

    def issue_view_payload(self, number: int, *, comments: bool = False) -> dict:
        row = self._find_issue(number)
        if row is None:
            raise RuntimeError(f"issue {number} not in fixture store")
        payload = {
            **row,
            "body": self.issue_bodies.get(number, row.get("body", "fixture body")),
            "author": {"login": "test"},
            "createdAt": "2026-01-01",
            "updatedAt": "2026-01-02",
        }
        if comments:
            payload["comments"] = list(self.issue_comments.get(number, []))
        return payload


@contextmanager
def patch_gh_stateful(workspace: Path) -> Iterator[StatefulGhStore]:
    """Stateful gh mock; yields store for assertions."""
    store = StatefulGhStore.from_workspace(workspace)

    def _run_json(self, args: list[str]):
        cmd = list(args)
        if cmd[:2] == ["issue", "list"]:
            state = "open"
            if "--state" in cmd:
                state = cmd[cmd.index("--state") + 1].lower()
            rows = copy.deepcopy(store.issues)
            if state == "open":
                return [r for r in rows if str(r.get("state", "OPEN")).upper() == "OPEN"]
            if state == "closed":
                return [r for r in rows if str(r.get("state", "OPEN")).upper() != "OPEN"]
            return rows
        if cmd[:2] == ["issue", "view"]:
            number = int(cmd[2])
            with_comments = "--comments" in cmd
            return store.issue_view_payload(number, comments=with_comments)
        if cmd[:2] == ["search", "issues"]:
            return copy.deepcopy(store.issues)
        if cmd[:2] == ["label", "list"]:
            return copy.deepcopy(store.labels)
        if cmd[:2] == ["pr", "list"]:
            return copy.deepcopy(store.prs)
        if cmd[:2] == ["pr", "view"]:
            number = int(cmd[2])
            for row in store.prs:
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
            title_idx = cmd.index("--title") + 1 if "--title" in cmd else None
            title = cmd[title_idx] if title_idx else "untitled"
            body = None
            if "--body" in cmd:
                body = cmd[cmd.index("--body") + 1]
            labels: list[str] = []
            if "--label" in cmd:
                labels = cmd[cmd.index("--label") + 1].split(",")
            url, _ = store.issue_create(title=title, body=body, labels=labels)
            return url
        if cmd[:2] == ["pr", "create"]:
            store.pr_create_calls.append(cmd)
            return "https://github.com/example/repo/pull/8"
        if cmd[:2] == ["pr", "diff"]:
            return "1 file changed, 10 insertions(+)"
        if cmd[0] == "issue" and cmd[1] in {"edit", "close", "delete", "comment"}:
            return ""
        if cmd[0] == "label" and cmd[1] in {"create", "delete"}:
            return ""
        if cmd[0] == "pr" and cmd[1] in {"edit", "close", "merge"}:
            return ""
        raise RuntimeError(f"unmocked gh run: {cmd}")

    with (
        patch("src.providers.gh.GhProvider.run_json", _run_json),
        patch("src.providers.gh.GhProvider.run", _run),
    ):
        yield store


@contextmanager
def patch_gh_all(workspace: Path) -> Iterator[None]:
    """Mock GhProvider reads/writes with fixture JSON (happy-path responses)."""
    with patch_gh_stateful(workspace):
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

    with patch("src.providers.gh.run_gh", _run_gh):
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
