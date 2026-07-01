"""AI subcommands — OpenCode tiers."""

from __future__ import annotations

import typer

from src.providers.opencode import OpenCodeProvider

ai_app = typer.Typer(help="AI via OpenCode (plan / summarize / code tiers).", no_args_is_help=True)


@ai_app.command("plan")
def ai_plan_cmd(
    prompt: str = typer.Argument(..., help="Planning prompt."),
) -> None:
    typer.echo(OpenCodeProvider().run_prompt(prompt, tier="plan", mode="shot"))


@ai_app.command("summarize")
def ai_summarize_cmd(
    prompt: str = typer.Argument(..., help="Text to summarize."),
) -> None:
    typer.echo(OpenCodeProvider().run_prompt(prompt, tier="summarize", mode="shot"))


@ai_app.command("code")
def ai_code_cmd(
    prompt: str = typer.Argument(..., help="Codegen prompt."),
    mode: str = typer.Option("shot", "--mode", help="shot or chat"),
) -> None:
    m = "chat" if mode == "chat" else "shot"
    typer.echo(OpenCodeProvider().run_prompt(prompt, tier="code", mode=m))


@ai_app.command("categorize")
def ai_categorize_cmd(
    prompt: str = typer.Argument(..., help="Categorization / issue-ship prompt."),
) -> None:
    typer.echo(OpenCodeProvider().run_prompt(prompt, tier="categorize", mode="shot"))
