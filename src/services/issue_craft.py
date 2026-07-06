"""Issue craft flows — dedupe, review, ship (@gh-issue / @gh-issue-review)."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any

from src.services.craft_ai import CraftAI
from src.services.gh_service import GhService

_PLAN_HEADING = re.compile(r"^##\s*\[cli\]\s*plan\s*$", re.IGNORECASE | re.MULTILINE)
_CHILDREN_HEADING = "## Subissues / Closure checklist"
_CHILDREN_SECTION = re.compile(
    r"^## (?:Children|Subissues) / Closure checklist\s*\n.*?(?=^##\s+|\Z)",
    re.MULTILINE | re.DOTALL,
)


class IssueCraftError(ValueError):
    """Raised when an issue cannot be used for the requested craft flow."""


def _open_inventory(svc: GhService, *, limit: int = 80) -> list[dict[str, Any]]:
    return svc.issue_list(state="open", limit=limit)


def review_issue(svc: GhService, number: int, *, ai: CraftAI | None = None) -> dict[str, Any]:
    ai = ai or CraftAI()
    ctx = svc.issue_context(number)
    report = ai.review_issue(context=ctx, open_issues=_open_inventory(svc))
    return {"number": number, "report": report, "context": ctx}


def _label_names(issue_or_context: dict[str, Any]) -> list[str]:
    if "labels" in issue_or_context and all(isinstance(lb, str) for lb in issue_or_context.get("labels", [])):
        return [str(lb) for lb in issue_or_context.get("labels", [])]
    labels = issue_or_context.get("labels") or issue_or_context.get("issue", {}).get("labels") or []
    names: list[str] = []
    for label in labels:
        if isinstance(label, dict):
            names.append(str(label.get("name", "")))
        else:
            names.append(str(label))
    return names


def require_epic_context(context: dict[str, Any]) -> str:
    labels = _label_names(context)
    slug = next((label for label in labels if label.startswith("epic:")), "")
    if "issue-type:epic" not in labels or not slug:
        number = context.get("issue", {}).get("number", "?")
        raise IssueCraftError(f"issue #{number} is not an epic issue")
    return slug


def require_child_context(context: dict[str, Any]) -> None:
    labels = _label_names(context)
    number = context.get("issue", {}).get("number", "?")
    if "issue-type:epic" in labels:
        raise IssueCraftError(f"issue #{number} is an epic issue; pick a subissue for PR work")


def render_epic_child_checklist(children: list[dict[str, Any]]) -> str:
    lines = [_CHILDREN_HEADING, ""]
    if not children:
        lines.append("_No subissues found._")
        return "\n".join(lines).rstrip() + "\n"
    for child in children:
        number = int(child["number"])
        title = str(child.get("title") or f"issue #{number}")
        state = str(child.get("state") or "OPEN").upper()
        checked = "x" if state == "CLOSED" else " "
        suffix = ""
        blocked_by = child.get("blocked_by") or []
        if blocked_by:
            suffix = " (blocked by " + ", ".join(f"#{n}" for n in blocked_by) + ")"
        lines.append(f"- [{checked}] #{number} {title}{suffix}")
    return "\n".join(lines).rstrip() + "\n"


def refresh_epic_checklist(body: str, children: list[dict[str, Any]]) -> str:
    checklist = render_epic_child_checklist(children)
    source = body.rstrip()
    if _CHILDREN_SECTION.search(source):
        return _CHILDREN_SECTION.sub(checklist.rstrip(), source).rstrip() + "\n"
    if not source:
        return checklist
    return f"{source}\n\n{checklist}"


def _children_for_epic(tree: dict[str, Any], *, epic_number: int, epic_slug: str) -> list[dict[str, Any]]:
    for parent in tree.get("parents") or []:
        if int(parent.get("number", 0)) == epic_number or parent.get("epic") == epic_slug:
            return list(parent.get("children") or [])
    return list((tree.get("epics") or {}).get(epic_slug, []))


def _all_children_for_epic(svc: GhService, *, epic_slug: str) -> list[dict[str, Any]]:
    rows = svc.issue_list(state="open", limit=200) + svc.issue_list(state="closed", limit=200)
    seen: set[int] = set()
    children: list[dict[str, Any]] = []
    for row in rows:
        number = int(row.get("number", 0))
        if number in seen:
            continue
        seen.add(number)
        labels = _label_names(row)
        if epic_slug in labels and "issue-type:child" in labels:
            children.append(
                {
                    "number": number,
                    "title": row.get("title"),
                    "url": row.get("url"),
                    "state": row.get("state", "OPEN"),
                    "labels": labels,
                }
            )
    return sorted(children, key=lambda child: (str(child.get("state", "")).upper() == "CLOSED", str(child.get("title", ""))))


def epic_closure_status(children: list[dict[str, Any]]) -> dict[str, Any]:
    open_children = [
        {"number": int(child["number"]), "title": child.get("title")}
        for child in children
        if str(child.get("state", "OPEN")).upper() != "CLOSED"
    ]
    return {
        "closeable": not open_children and bool(children),
        "open_children": open_children,
        "total_children": len(children),
    }


def review_epic(
    svc: GhService,
    number: int,
    *,
    runtime: str,
    yes: bool = False,
    ai: CraftAI | None = None,
) -> dict[str, Any]:
    ai = ai or CraftAI()
    epic_context = svc.issue_context(number)
    epic_slug = require_epic_context(epic_context)
    tree = svc.backlog_tree()
    children = _all_children_for_epic(svc, epic_slug=epic_slug)
    if not children:
        children = _children_for_epic(tree, epic_number=number, epic_slug=epic_slug)
    child_contexts = [svc.issue_context(int(child["number"])) for child in children]
    report = ai.review_epic(epic_context=epic_context, children=child_contexts, backlog=tree)
    child_plans = [
        {
            "number": int(child_ctx["issue"]["number"]),
            "body": ai.plan_issue(context=child_ctx, runtime=runtime),
        }
        for child_ctx in child_contexts
    ]
    checklist_body = refresh_epic_checklist(str(epic_context.get("issue", {}).get("body", "")), children)
    result: dict[str, Any] = {
        "number": number,
        "epic": epic_slug,
        "children": children,
        "checklist_body": checklist_body,
        "closure": epic_closure_status(children),
        "report": report,
        "child_plans": child_plans,
        "dry_run": not yes,
    }
    if not yes:
        return result

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md") as body_file:
        body_file.write(checklist_body)
        body_file.flush()
        svc.issue_edit(number, body_file=Path(body_file.name))
    svc.issue_comment(number, body=f"## [cli] epic refinement\n\n{report}")
    for child_plan in child_plans:
        svc.issue_comment(int(child_plan["number"]), body=f"## [cli] plan\n\n{child_plan['body']}")
    return result


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
