"""AI subcommands — backward-compatible alias for `cli opencode`."""

from __future__ import annotations

import typer

from src.providers.opencode import OpenCodeProvider

ai_app = typer.Typer(help="(alias) use: cli opencode", no_args_is_help=True, hidden=True)


@ai_app.command("plan")
def ai_plan_cmd(prompt: str = typer.Argument(...)) -> None:
    typer.echo(OpenCodeProvider().run_prompt(prompt, tier="plan", mode="shot"))


@ai_app.command("summarize")
def ai_summarize_cmd(prompt: str = typer.Argument(...)) -> None:
    typer.echo(OpenCodeProvider().run_prompt(prompt, tier="summarize", mode="shot"))


@ai_app.command("code")
def ai_code_cmd(
    prompt: str = typer.Argument(...),
    mode: str = typer.Option("shot", "--mode"),
) -> None:
    m = "chat" if mode == "chat" else "shot"
    typer.echo(OpenCodeProvider().run_prompt(prompt, tier="code", mode=m))


@ai_app.command("categorize")
def ai_categorize_cmd(prompt: str = typer.Argument(...)) -> None:
    typer.echo(OpenCodeProvider().run_prompt(prompt, tier="categorize", mode="shot"))
