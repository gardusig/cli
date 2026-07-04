"""Review PR — backward-compatible alias for `cli opencode gh review`."""

from __future__ import annotations

import typer

from src.commands.craft import gh_review_pr_cmd

review_app = typer.Typer(help="(alias) use: cli opencode gh review", no_args_is_help=True, hidden=True)


@review_app.command("pr")
def review_pr_cmd(
    ctx: typer.Context,
    number: int = typer.Argument(..., help="PR number."),
    issue: int | None = typer.Option(None, "--issue", "-i"),
    comment: bool = typer.Option(True, "--comment/--no-comment"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    gh_review_pr_cmd(ctx, number, issue=issue, comment=comment, yes=yes)


@review_app.callback()
def review_root(
    ctx: typer.Context,
    repo: str | None = typer.Option(None, "--repo"),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["repo"] = repo
