"""PR craft flows — @gh-pr / @gh-pr-review."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from src.services.craft_ai import CraftAI
from src.services.gh_service import GhService
from src.services.git_shortcuts import GitShortcuts
from src.services.issue_craft import find_plan_text

_ROOT = Path(__file__).resolve().parents[2]
_ISSUE_REF = re.compile(r"#(\d+)")


def _linked_issue_numbers(pr_view: dict[str, Any], issue_ctx: dict[str, Any] | None) -> list[int]:
    nums: set[int] = set()
    if issue_ctx:
        nums.add(int(issue_ctx["issue"]["number"]))
    blob = json.dumps(pr_view, default=str)
    for m in _ISSUE_REF.finditer(blob):
        nums.add(int(m.group(1)))
    return sorted(nums)


def review_pr(
    svc: GhService,
    number: int,
    *,
    ai: CraftAI | None = None,
    primary_issue: int | None = None,
) -> dict[str, Any]:
    ai = ai or CraftAI()
    pr_view = svc.pr_view(number)
    diff = svc.pr_diff(number)
    linked: list[dict[str, Any]] = []
    for num in _linked_issue_numbers(pr_view, None):
        if primary_issue and num != primary_issue:
            continue
        try:
            linked.append(svc.issue_context(num))
        except Exception:
            continue
    if primary_issue and not linked:
        linked.append(svc.issue_context(primary_issue))
    summary = ai.review_pr(pr_view=pr_view, diff=diff, linked_issues=linked)
    return {
        "number": number,
        "summary": summary,
        "view": pr_view,
        "linked_issues": [i.get("issue", {}).get("number") for i in linked],
    }


def branch_name_for_issue(number: int, title: str) -> str:
    slug = title.split("—")[-1].strip().lower().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)[:40] or "work"
    return f"craft/{number}-{slug}"


def craft_pr(
    svc: GhService,
    git: GitShortcuts,
    number: int,
    *,
    branch: str | None = None,
    skip_test: bool = False,
    ai: CraftAI | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """@gh-pr + @gh-issue-execute handoff: branch → guidance → test → push → PR."""
    ai = ai or CraftAI()
    root = repo_root or _ROOT
    ctx = svc.issue_context(number)
    title = str(ctx.get("issue", {}).get("title", f"issue-{number}"))
    br = branch or branch_name_for_issue(number, title)
    plan_text = find_plan_text(ctx)

    git.start(br, yes=True)
    guidance = ai.code_guidance(context=ctx, title=title)
    guidance_path = root / ".cursor" / "gh" / "craft" / f"issue-{number}-guidance.md"
    guidance_path.parent.mkdir(parents=True, exist_ok=True)
    guidance_path.write_text(guidance, encoding="utf-8")

    if not skip_test and (root / "scripts" / "test" / "all.sh").is_file():
        subprocess.run(["bash", str(root / "scripts" / "test" / "all.sh")], cwd=root, check=True)

    git.commit(message=f"Craft PR for #{number}")
    git.push(yes=True)

    diff_stat = ""
    try:
        diff_stat = subprocess.check_output(
            ["git", "diff", "main...HEAD", "--stat"],
            cwd=root,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    body = ai.pr_body(issue_context=ctx, diff_stat=diff_stat)
    if plan_text:
        body = f"{body}\n\n## Plan reference\n\n{plan_text[:4000]}"

    pr = svc.pr_create(title=title, body=body, head=br)
    svc.issue_comment(
        number,
        body=(
            f"## [cli] outcome\n\n"
            f"- PR: {pr.get('url', pr)}\n"
            f"- branch: `{br}`\n"
            f"- guidance: `{guidance_path.relative_to(root)}`"
        ),
    )
    return {
        "issue": number,
        "branch": br,
        "pr": pr,
        "guidance_file": str(guidance_path),
    }


def execute_issue(
    svc: GhService,
    number: int,
    *,
    ai: CraftAI | None = None,
    handoff_pr: bool = False,
    git: GitShortcuts | None = None,
    skip_test: bool = False,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """@gh-issue-execute: run plan checkpoints, optional craft pr handoff."""
    ai = ai or CraftAI()
    ctx = svc.issue_context(number)
    plan_text = find_plan_text(ctx)
    report = ai.execute_issue(context=ctx, plan_text=plan_text)
    result: dict[str, Any] = {"number": number, "report": report, "plan_found": bool(plan_text)}
    if handoff_pr and git is not None:
        result["pr"] = craft_pr(
            svc,
            git,
            number,
            skip_test=skip_test,
            ai=ai,
            repo_root=repo_root,
        )
    return result
