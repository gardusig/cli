"""Review PR — diff, checks, AI summary (no merge)."""

from __future__ import annotations

import json

import typer

from src.providers.opencode import OpenCodeProvider
from src.services.gh_service import GhService

review_app = typer.Typer(help="Review pull requests (no merge).", no_args_is_help=True)


def _svc(repo: str | None) -> GhService:
    return GhService(repo=repo)


@review_app.command("pr")
def review_pr_cmd(
    ctx: typer.Context,
    number: int = typer.Argument(..., help="PR number."),
    comment: bool = typer.Option(True, "--comment/--no-comment", help="Post review summary."),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    repo = (ctx.obj or {}).get("repo") if ctx.obj else None
    svc = _svc(repo)
    view = svc.pr_view(number)
    diff = svc.pr_diff(number)
    summary = OpenCodeProvider().run_prompt(
        f"Review PR #{number}:\n{json.dumps(view)[:4000]}\n\nDiff:\n{diff[:12000]}",
        tier="summarize",
    )
    result = {"number": number, "summary": summary, "view": view}
    typer.echo(json.dumps(result, indent=2))
    if comment:
        from src.internal.write.gate import require_write_gate

        require_write_gate("review-pr", svc.snapshot_summary(), yes=yes)
        svc.pr_comment(number, body=f"## [cli] review\n\n{summary}")


@review_app.callback()
def review_root(
    ctx: typer.Context,
    repo: str | None = typer.Option(None, "--repo"),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["repo"] = repo
