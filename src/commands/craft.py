"""Craft commands — issue triage, PR creation, headless operator flows."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import typer

from src.internal.write.gate import require_write_gate
from src.providers.opencode import OpenCodeProvider
from src.services.gh_service import GhService
from src.services.git_shortcuts import GitShortcuts

craft_app = typer.Typer(help="Craft issues and PRs (headless operator).", no_args_is_help=True)

_ROOT = Path(__file__).resolve().parents[2]


def _svc(repo: str | None) -> GhService:
    return GhService(repo=repo)


@craft_app.command("issue")
def craft_issue_cmd(
    ctx: typer.Context,
    number: int | None = typer.Option(None, "--number", "-n", help="Issue to plan/review."),
    review: bool = typer.Option(False, "--review", help="Read-only reshape report."),
    plan: bool = typer.Option(False, "--plan", help="Append ## [cli] plan comment via AI."),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    repo = (ctx.obj or {}).get("repo") if ctx.obj else None
    svc = _svc(repo)
    if number is None:
        nxt = svc.backlog_next()
        if not nxt:
            typer.echo("No ready backlog child.")
            raise typer.Exit(1)
        number = int(nxt["number"])
    ctx_data = svc.issue_context(number)
    typer.echo(json.dumps(ctx_data, indent=2))
    if review:
        return
    if plan:
        require_write_gate("craft-issue-plan", svc.snapshot_summary(), yes=yes)
        body = OpenCodeProvider().run_prompt(
            f"Plan implementation for issue #{number}:\n{json.dumps(ctx_data)[:8000]}",
            tier="plan",
        )
        svc.issue_comment(number, body=f"## [cli] plan\n\n{body}")


@craft_app.command("pr")
def craft_pr_cmd(
    ctx: typer.Context,
    number: int | None = typer.Option(None, "--number", "-n", help="Issue to implement."),
    branch: str | None = typer.Option(None, "--branch", help="Branch name (default from issue)."),
    skip_test: bool = typer.Option(False, "--skip-test"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    repo = (ctx.obj or {}).get("repo") if ctx.obj else None
    svc = _svc(repo)
    git = GitShortcuts()
    if number is None:
        nxt = svc.backlog_next()
        if not nxt:
            typer.echo("No ready backlog child.")
            raise typer.Exit(1)
        number = int(nxt["number"])
    ctx_data = svc.issue_context(number)
    title = str(ctx_data.get("issue", {}).get("title", f"issue-{number}"))
    br = branch or f"craft/{number}-" + title.split("—")[-1].strip().lower().replace(" ", "-")[:40]
    require_write_gate(
        "craft-pr",
        [*svc.snapshot_summary(), f"issue: #{number}", f"branch: {br}"],
        yes=yes,
    )
    git.start(br, yes=True)
    prompt = f"Implement issue #{number}: {title}\n\nContext:\n{json.dumps(ctx_data)[:6000]}"
    OpenCodeProvider().run_prompt(prompt, tier="code", mode="chat")
    if not skip_test:
        subprocess.run(["bash", str(_ROOT / "scripts" / "test" / "all.sh")], cwd=_ROOT, check=True)
    git.commit(message=f"Craft PR for #{number}")
    git.push(yes=True)
    summary = OpenCodeProvider().run_prompt(
        f"Write a PR body for issue #{number}: {title}",
        tier="summarize",
    )
    pr = svc.pr_create(
        title=title,
        body=summary,
        head=br,
    )
    svc.issue_comment(
        number,
        body=f"## [cli] outcome\n\n- PR: {pr.get('url', pr)}\n- branch: `{br}`",
    )
    typer.echo(json.dumps(pr, indent=2))


@craft_app.callback()
def craft_root(
    ctx: typer.Context,
    repo: str | None = typer.Option(None, "--repo", help="owner/name"),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["repo"] = repo
