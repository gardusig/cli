"""Review PR — @gh-pr-review via DeepSeek reasoner (no merge)."""

from __future__ import annotations

import json

import typer

from src.internal.write.gate import require_write_gate
from src.services.gh_service import GhService
from src.services.pr_craft import review_pr

review_app = typer.Typer(help="Review pull requests (no merge).", no_args_is_help=True)


def _svc(repo: str | None) -> GhService:
    return GhService(repo=repo)


@review_app.command("pr")
def review_pr_cmd(
    ctx: typer.Context,
    number: int = typer.Argument(..., help="PR number."),
    issue: int | None = typer.Option(None, "--issue", "-i", help="Primary linked issue #."),
    comment: bool = typer.Option(True, "--comment/--no-comment", help="Post review summary."),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    repo = (ctx.obj or {}).get("repo") if ctx.obj else None
    svc = _svc(repo)
    result = review_pr(svc, number, primary_issue=issue)
    typer.echo(json.dumps(result, indent=2))
    if comment:
        require_write_gate("review-pr", svc.snapshot_summary(), yes=yes)
        svc.pr_comment(number, body=f"## [cli] review\n\n{result['summary']}")


@review_app.callback()
def review_root(
    ctx: typer.Context,
    repo: str | None = typer.Option(None, "--repo"),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["repo"] = repo
