"""Issue craft flows — dedupe, review, ship (@gh-issue / @gh-issue-review)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from src.services.craft_ai import CraftAI
from src.services.gh_service import GhService

_PLAN_HEADING = re.compile(r"^##\s*\[cli\]\s*plan\s*$", re.IGNORECASE | re.MULTILINE)


def _open_inventory(svc: GhService, *, limit: int = 80) -> list[dict[str, Any]]:
    return svc.issue_list(state="open", limit=limit)


def review_issue(svc: GhService, number: int, *, ai: CraftAI | None = None) -> dict[str, Any]:
    ai = ai or CraftAI()
    ctx = svc.issue_context(number)
    report = ai.review_issue(context=ctx, open_issues=_open_inventory(svc))
    return {"number": number, "report": report, "context": ctx}


def dedupe_candidate(
    svc: GhService,
    *,
    title: str,
    body: str,
    self_number: int | None = None,
    ai: CraftAI | None = None,
) -> dict[str, Any]:
    ai = ai or CraftAI()
    verdict = ai.dedupe(
        title=title,
        body=body,
        open_issues=_open_inventory(svc),
        self_number=self_number,
    )
    return verdict


def ship_issue(
    svc: GhService,
    *,
    title: str,
    body: str,
    yes: bool = False,
    edit_number: int | None = None,
    ai: CraftAI | None = None,
) -> dict[str, Any]:
    """@gh-issue router: dedupe → spec → create or edit."""
    ai = ai or CraftAI()
    dedupe = dedupe_candidate(svc, title=title, body=body, self_number=edit_number, ai=ai)
    spec = ai.ship_spec(
        title=title,
        body=body,
        dedupe=dedupe,
        repo=svc.repo_display(),
        backlog=svc.backlog_tree(),
    )

    action = spec.get("action", "create")
    target_num = edit_number or spec.get("edit_number")
    if dedupe.get("verdict") == "likely_duplicate" and dedupe.get("duplicate_number"):
        action = "edit"
        target_num = int(dedupe["duplicate_number"])

    result: dict[str, Any] = {
        "dedupe": dedupe,
        "spec": spec,
        "action": action,
        "dry_run": not yes,
    }

    if not yes:
        return result

    final_title = str(spec.get("title") or title)
    final_body = str(spec.get("body") or body)
    labels = [str(lb) for lb in spec.get("labels") or []]

    if action == "edit" and target_num:
        svc.issue_edit(int(target_num), title=final_title, add_labels=labels or None)
        if final_body:
            svc.issue_comment(int(target_num), body=f"## [cli] reshape\n\n{final_body}")
        result["issue"] = {"number": int(target_num), "action": "edit"}
    else:
        created = svc.issue_create(title=final_title, body=final_body, labels=labels or None)
        result["issue"] = {**created, "action": "create"}
    return result


def plan_issue(
    svc: GhService,
    number: int,
    *,
    runtime: str,
    ai: CraftAI | None = None,
) -> str:
    ai = ai or CraftAI()
    ctx = svc.issue_context(number)
    return ai.plan_issue(context=ctx, runtime=runtime)


def find_plan_text(context: dict[str, Any]) -> str:
    """Extract latest [cli] plan from comments or issue body."""
    chunks: list[str] = []
    body = str(context.get("issue", {}).get("body", ""))
    if _PLAN_HEADING.search(body):
        chunks.append(body)
    for comment in reversed(context.get("comments") or []):
        text = str(comment.get("body", ""))
        if _PLAN_HEADING.search(text) or "## Goal" in text:
            chunks.append(text)
            break
    return chunks[0] if chunks else body


def pick_issues(
    svc: GhService,
    *,
    label: list[str] | None = None,
    limit: int = 30,
) -> list[dict[str, Any]]:
    return svc.issue_list(state="open", label=label, limit=limit)


def write_draft(path: Path, *, title: str, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body}\n", encoding="utf-8")
    return path
