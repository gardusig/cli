"""GitHub domain — AI-assisted issues, PRs, and review (OpenCode + DeepSeek)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from src.internal.write.gate import require_write_gate
from src.services.craft_ai import CraftAI
from src.services.gh_service import GhService
from src.services.git_shortcuts import GitShortcuts
from src.services.issue_craft import (
    IssueCraftError,
    dedupe_candidate,
    pick_issues,
    review_epic,
    plan_issue,
    review_issue,
    ship_issue,
    write_draft,
)
from src.services.pr_craft import craft_pr, execute_issue, pr_execution_plan, review_pr
from src.utils.runtime_profile import detect_profile, is_headless

gh_domain_app = typer.Typer(
    help="GitHub AI flows — issues, PRs, review (no merge).",
    no_args_is_help=True,
)

# Backward-compatible alias
craft_app = gh_domain_app

_ROOT = Path(__file__).resolve().parents[2]


def _truthy(value: str | bool | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _svc(repo: str | None) -> GhService:
    return GhService(repo=repo)


def _repo(ctx: typer.Context) -> str | None:
    return (ctx.obj or {}).get("repo") if ctx.obj else None


@gh_domain_app.command("issue")
def craft_issue_cmd(
    ctx: typer.Context,
    number: int | None = typer.Option(None, "--number", "-n", help="Issue to plan/review/edit."),
    title: str | None = typer.Option(None, "--title", "-t", help="New issue title (ship mode)."),
    body: str | None = typer.Option(None, "--body", "-b", help="Issue body markdown."),
    body_file: Path | None = typer.Option(None, "--body-file", help="Issue body file."),
    review: bool = typer.Option(False, "--review", help="Read-only reshape report."),
    plan: bool = typer.Option(False, "--plan", help="Generate implementation plan."),
    plan_only: bool = typer.Option(
        False,
        "--plan-only",
        help="Print plan to stdout; no GitHub comment.",
    ),
    dedupe_only: bool = typer.Option(False, "--dedupe-only", help="Run dedupe verdict only."),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Plan, review, ship, or show GitHub issues."""
    repo = _repo(ctx)
    svc = _svc(repo)
    ai = CraftAI()

    if number is None and not title and not body and not body_file:
        nxt = svc.backlog_next()
        if not nxt:
            typer.echo("No ready backlog subissue. Use --number or --title.", err=True)
            raise typer.Exit(1)
        number = int(nxt["number"])

    if number is not None and review:
        result = review_issue(svc, number, ai=ai)
        typer.echo(json.dumps({"report": result["report"]}, indent=2))
        return

    if number is not None and (plan or plan_only):
        body_text = plan_issue(svc, number, runtime=detect_profile().value, ai=ai)
        if plan_only or is_headless():
            typer.echo(body_text)
            if plan_only:
                return
        if not yes and not plan_only:
            typer.echo(
                "\n(headless — pass --yes to comment plan on issue)",
                err=True,
            )
            return
        require_write_gate("craft-issue-plan", svc.snapshot_summary(), yes=yes)
        svc.issue_comment(number, body=f"## [cli] plan\n\n{body_text}")
        return

    if number is not None and not title and not body and not body_file:
        ctx_data = svc.issue_context(number)
        typer.echo(json.dumps(ctx_data, indent=2))
        return

    issue_body = body or ""
    if body_file:
        issue_body = body_file.read_text(encoding="utf-8")
    if not issue_body and not sys.stdin.isatty():
        issue_body = sys.stdin.read()

    if not title:
        typer.echo("Provide --title for ship mode.", err=True)
        raise typer.Exit(1)

    if dedupe_only:
        verdict = dedupe_candidate(svc, title=title, body=issue_body, ai=ai)
        typer.echo(json.dumps(verdict, indent=2))
        return

    summary = [
        *svc.snapshot_summary(),
        f"title: {title}",
        f"body_chars: {len(issue_body)}",
    ]
    require_write_gate("craft-issue", summary, yes=yes)
    result = ship_issue(svc, title=title, body=issue_body, yes=yes, edit_number=number, ai=ai)
    typer.echo(json.dumps(result, indent=2))


@gh_domain_app.command("pick")
def craft_pick_cmd(
    ctx: typer.Context,
    label: list[str] | None = typer.Option(None, "--label", "-l", help="Filter labels."),
    limit: int = typer.Option(30, "--limit"),
    number: int | None = typer.Option(None, "--number", "-n", help="Pick this issue and show context."),
) -> None:
    """List open issues; with --number show full context."""
    repo = _repo(ctx)
    svc = _svc(repo)
    if number is not None:
        typer.echo(json.dumps(svc.issue_context(number), indent=2))
        return
    issues = pick_issues(svc, label=label, limit=limit)
    typer.echo(json.dumps({"repo": svc.repo_display(), "issues": issues}, indent=2))


@gh_domain_app.command("epic")
def craft_epic_cmd(
    ctx: typer.Context,
    number: int = typer.Option(..., "--number", "-n", help="Epic issue to refine."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Render refinement without GitHub writes."),
    dry_run_value: str | None = typer.Option(None, "--dry-run-value", help="Pipeline boolean value for dry-run."),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Refine an epic issue and its subissues into executable issue plans."""
    repo = _repo(ctx)
    svc = _svc(repo)
    if dry_run_value is not None:
        dry_run = _truthy(dry_run_value, default=True)
    if not dry_run:
        require_write_gate(
            "craft-epic-refine",
            [*svc.snapshot_summary(), f"epic: #{number}", "writes: epic body + issue comments"],
            yes=yes,
        )
    try:
        result = review_epic(
            svc,
            number,
            runtime=detect_profile().value,
            yes=not dry_run,
        )
    except IssueCraftError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(json.dumps(result, indent=2))


@gh_domain_app.command("next")
def craft_next_cmd(ctx: typer.Context) -> None:
    """Topo backlog next + issue context."""
    repo = _repo(ctx)
    svc = _svc(repo)
    nxt = svc.backlog_next()
    if not nxt:
        typer.echo(json.dumps({"ready": False}, indent=2))
        raise typer.Exit(1)
    ctx_data = svc.issue_context(int(nxt["number"]))
    typer.echo(json.dumps({"next": nxt, "context": ctx_data}, indent=2))


@gh_domain_app.command("pr-plan")
def craft_pr_plan_cmd(
    ctx: typer.Context,
    number: int | None = typer.Option(None, "--number", "-n", help="Subissue to implement."),
    branch: str | None = typer.Option(None, "--branch"),
) -> None:
    """Render a non-mutating PR execution plan for a subissue."""
    repo = _repo(ctx)
    svc = _svc(repo)
    if number is None:
        nxt = svc.backlog_next()
        if not nxt:
            typer.echo("No ready backlog subissue.", err=True)
            raise typer.Exit(1)
        number = int(nxt["number"])
    try:
        result = pr_execution_plan(svc, number, branch=branch)
    except IssueCraftError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(json.dumps(result, indent=2))


@gh_domain_app.command("issue-to-pr")
def craft_issue_to_pr_cmd(
    ctx: typer.Context,
    number: str | None = typer.Option(None, "--number", "-n", help="Subissue to implement."),
    branch: str | None = typer.Option(None, "--branch"),
    dry_run: str = typer.Option("true", "--dry-run", help="true renders a PR plan; false creates the PR."),
    repo_root: Path = typer.Option(Path("."), "--repo-root", help="Repository root for PR work."),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Pipeline entry point: pick a subissue, then plan or create its PR."""
    repo = _repo(ctx)
    svc = _svc(repo)
    issue_number = int(number) if number and number.strip() else None
    selected_branch = branch if branch and branch.strip() else None
    if issue_number is None:
        nxt = svc.backlog_next()
        if not nxt:
            typer.echo("No ready backlog subissue.", err=True)
            raise typer.Exit(1)
        issue_number = int(nxt["number"])
    if _truthy(dry_run, default=True):
        try:
            result = pr_execution_plan(svc, issue_number, branch=selected_branch)
        except IssueCraftError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(1) from exc
        typer.echo(json.dumps(result, indent=2))
        return

    root = repo_root.resolve()
    ctx_data = svc.issue_context(issue_number)
    title = str(ctx_data.get("issue", {}).get("title", f"issue-{issue_number}"))
    br = selected_branch or f"craft/{issue_number}-" + title.split("—")[-1].strip().lower().replace(" ", "-")[:40]
    require_write_gate(
        "craft-issue-to-pr",
        [*svc.snapshot_summary(), f"subissue: #{issue_number}", f"branch: {br}"],
        yes=yes,
    )
    try:
        result = craft_pr(
            svc,
            GitShortcuts(top=str(root)),
            issue_number,
            branch=br,
            repo_root=root,
        )
    except IssueCraftError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(json.dumps(result, indent=2))


@gh_domain_app.command("execute")
def craft_execute_cmd(
    ctx: typer.Context,
    number: int = typer.Argument(..., help="Issue to execute."),
    pr: bool = typer.Option(False, "--pr", help="Hand off to craft pr after checkpoints."),
    skip_test: bool = typer.Option(False, "--skip-test"),
    repo_root: Path = typer.Option(Path("."), "--repo-root", help="Repository root for PR work."),
    comment: bool = typer.Option(True, "--comment/--no-comment"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Execute issue checkpoints; optional --pr handoff."""
    repo = _repo(ctx)
    svc = _svc(repo)
    root = repo_root.resolve()
    if pr:
        require_write_gate(
            "craft-execute-pr",
            [*svc.snapshot_summary(), f"issue: #{number}", "handoff: craft pr"],
            yes=yes,
        )
    result = execute_issue(
        svc,
        number,
        handoff_pr=pr,
        git=GitShortcuts(top=str(root)) if pr else None,
        skip_test=skip_test,
        repo_root=root,
    )
    if comment and not pr:
        require_write_gate("craft-execute", svc.snapshot_summary(), yes=yes)
        svc.issue_comment(number, body=f"## [cli] execute\n\n{result['report']}")
    typer.echo(json.dumps(result, indent=2))


@gh_domain_app.command("pr")
def craft_pr_cmd(
    ctx: typer.Context,
    number: int | None = typer.Option(None, "--number", "-n", help="Issue to implement."),
    branch: str | None = typer.Option(None, "--branch"),
    skip_test: bool = typer.Option(False, "--skip-test"),
    repo_root: Path = typer.Option(Path("."), "--repo-root", help="Repository root for PR work."),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Branch, codegen guidance, test, push, open PR."""
    repo = _repo(ctx)
    svc = _svc(repo)
    root = repo_root.resolve()
    git = GitShortcuts(top=str(root))
    if number is None:
        nxt = svc.backlog_next()
        if not nxt:
            typer.echo("No ready backlog subissue.", err=True)
            raise typer.Exit(1)
        number = int(nxt["number"])
    ctx_data = svc.issue_context(number)
    title = str(ctx_data.get("issue", {}).get("title", f"issue-{number}"))
    br = branch or f"craft/{number}-" + title.split("—")[-1].strip().lower().replace(" ", "-")[:40]
    require_write_gate(
        "craft-pr",
        [
            *svc.snapshot_summary(),
            f"issue: #{number}",
            f"branch: {br}",
        ],
        yes=yes,
    )
    try:
        pr_result = craft_pr(
            svc,
            git,
            number,
            branch=br,
            skip_test=skip_test,
            repo_root=root,
        )
    except IssueCraftError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(json.dumps(pr_result, indent=2))


@gh_domain_app.command("draft")
def craft_draft_cmd(
    title: str = typer.Argument(...),
    body_file: Path = typer.Option(..., "--body-file", exists=True),
    slug: str = typer.Option("draft", "--slug"),
) -> None:
    """Write issue draft under .cursor/gh/issue/ (no GitHub writes)."""
    body = body_file.read_text(encoding="utf-8")
    path = _ROOT / ".cursor" / "gh" / "issue" / f"{slug}.md"
    write_draft(path, title=title, body=body)
    typer.echo(json.dumps({"path": str(path)}, indent=2))


@gh_domain_app.command("review")
def gh_review_pr_cmd(
    ctx: typer.Context,
    number: int = typer.Argument(..., help="PR number."),
    issue: int | None = typer.Option(None, "--issue", "-i", help="Primary linked issue #."),
    comment: bool = typer.Option(True, "--comment/--no-comment", help="Post review summary."),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """AI PR review vs linked issues (no merge)."""
    repo = _repo(ctx)
    svc = _svc(repo)
    result = review_pr(svc, number, primary_issue=issue)
    typer.echo(json.dumps(result, indent=2))
    if comment:
        require_write_gate("review-pr", svc.snapshot_summary(), yes=yes)
        svc.pr_comment(number, body=f"## [cli] review\n\n{result['summary']}")


@gh_domain_app.callback()
def gh_domain_root(
    ctx: typer.Context,
    repo: str | None = typer.Option(None, "--repo", help="owner/name"),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["repo"] = repo
