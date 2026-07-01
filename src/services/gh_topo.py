"""Topological backlog: priority:N epics, step — children, Depends edges."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_STEP_RE = re.compile(r"^(?P<step>\d+)\s*[—\-]\s*(?P<rest>.+)$")
_PRIORITY_RE = re.compile(r"^priority:(?P<n>[0-5])$")
_DEPENDS_RE = re.compile(r"(?:Depends|Blocked-by):\s*#(?P<num>\d+)", re.IGNORECASE)


@dataclass(frozen=True, order=True)
class StepKey:
    step: int

    @classmethod
    def from_title(cls, title: str) -> StepKey | None:
        m = _STEP_RE.match(title.strip())
        if m:
            return cls(int(m.group("step")))
        return None


def _label_names(issue: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for lb in issue.get("labels", []):
        if isinstance(lb, dict):
            out.append(str(lb.get("name", "")))
        else:
            out.append(str(lb))
    return out


def epic_priority(issue: dict[str, Any]) -> int | None:
    for name in _label_names(issue):
        m = _PRIORITY_RE.match(name)
        if m:
            return int(m.group("n"))
    for name in _label_names(issue):
        if name == "p0":
            return 0
        if name == "p1":
            return 1
        if name == "p2":
            return 2
    return None


def epic_slug(issue: dict[str, Any]) -> str | None:
    for name in _label_names(issue):
        if name.startswith("epic:"):
            return name
    return None


def depends_on(comments: list[dict[str, Any]] | None, body: str = "") -> set[int]:
    nums: set[int] = set()
    text = body or ""
    for c in comments or []:
        text += "\n" + str(c.get("body", ""))
    for m in _DEPENDS_RE.finditer(text):
        nums.add(int(m.group("num")))
    return nums


def ambiguity_score(issue: dict[str, Any], comments: list[dict[str, Any]] | None = None) -> int:
    score = 0
    title = str(issue.get("title", ""))
    labels = _label_names(issue)
    if "question" in labels or "?" in title:
        score += 2
    blob = title
    for c in comments or []:
        blob += str(c.get("body", ""))
    for token in ("⚠️", "blocked", "TBD"):
        score += 3 * blob.lower().count(token.lower())
    if "## Acceptance" not in blob and "## Done when" not in blob:
        score += 2
    if len(title.split()) < 4 or len(title) > 120:
        score += 1
    return score


def closed_numbers(issues: list[dict[str, Any]]) -> set[int]:
    return {int(i["number"]) for i in issues if str(i.get("state", "")).upper() == "CLOSED"}


def is_child_ready(
    issue: dict[str, Any],
    *,
    closed: set[int],
    comments: list[dict[str, Any]] | None = None,
) -> bool:
    deps = depends_on(comments, str(issue.get("body", "")))
    return all(n in closed for n in deps)


def sort_children(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(issue: dict[str, Any]) -> tuple[int, int, str]:
        step = StepKey.from_title(str(issue.get("title", "")))
        step_n = step.step if step else 999_999
        return (step_n, ambiguity_score(issue), str(issue.get("title", "")).lower())

    return sorted(issues, key=key)


def pick_next_child(
    issues: list[dict[str, Any]],
    *,
    issue_comments: dict[int, list[dict[str, Any]]] | None = None,
) -> dict[str, Any] | None:
    """Pick lowest-priority epic with a ready child; then lowest step."""
    open_issues = [i for i in issues if str(i.get("state", "OPEN")).upper() == "OPEN"]
    closed = closed_numbers(issues)
    comments_map = issue_comments or {}

    epics: list[dict[str, Any]] = []
    children_by_epic: dict[str, list[dict[str, Any]]] = {}

    for issue in open_issues:
        labels = _label_names(issue)
        slug = epic_slug(issue)
        if "issue-type:epic" in labels or (slug and StepKey.from_title(str(issue.get("title", ""))) is None and "issue-type:child" not in labels):
            if slug:
                epics.append(issue)
        elif "issue-type:child" in labels and slug:
            children_by_epic.setdefault(slug, []).append(issue)
        elif StepKey.from_title(str(issue.get("title", ""))):
            children_by_epic.setdefault("_unlabeled", []).append(issue)

    epics.sort(key=lambda e: (epic_priority(e) if epic_priority(e) is not None else 9, str(e.get("title", ""))))

    for epic in epics:
        slug = epic_slug(epic)
        if not slug:
            continue
        children = children_by_epic.get(slug, [])
        ready = [
            c
            for c in children
            if is_child_ready(c, closed=closed, comments=comments_map.get(int(c["number"])))
        ]
        if ready:
            pick = sort_children(ready)[0]
            step = StepKey.from_title(str(pick.get("title", "")))
            return {
                "number": pick["number"],
                "title": pick["title"],
                "url": pick.get("url"),
                "epic": slug,
                "priority": epic_priority(epic),
                "step": step.step if step else None,
            }

    unlabeled = children_by_epic.get("_unlabeled", [])
    if unlabeled:
        pick = sort_children(unlabeled)[0]
        step = StepKey.from_title(str(pick.get("title", "")))
        return {
            "number": pick["number"],
            "title": pick["title"],
            "url": pick.get("url"),
            "step": step.step if step else None,
        }
    return None
