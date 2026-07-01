"""OpenCode — AI entry point (DeepSeek roles + domain commands)."""

from __future__ import annotations

import typer

from src.commands.chat import chat_app
from src.commands.craft import gh_domain_app
from src.providers.opencode import OpenCodeProvider

opencode_app = typer.Typer(
    help="AI via OpenCode — raw prompts, chat, and domain flows (gh).",
    no_args_is_help=True,
)

opencode_app.add_typer(chat_app, name="chat")
opencode_app.add_typer(gh_domain_app, name="gh")


@opencode_app.command("plan")
def opencode_plan_cmd(prompt: str = typer.Argument(..., help="Planning / reasoning prompt.")) -> None:
    typer.echo(OpenCodeProvider().run_prompt(prompt, tier="plan", mode="shot"))


@opencode_app.command("summarize")
def opencode_summarize_cmd(prompt: str = typer.Argument(..., help="Text to summarize.")) -> None:
    typer.echo(OpenCodeProvider().run_prompt(prompt, tier="summarize", mode="shot"))


@opencode_app.command("code")
def opencode_code_cmd(
    prompt: str = typer.Argument(..., help="Codegen prompt."),
    mode: str = typer.Option("shot", "--mode", help="shot or chat"),
) -> None:
    m = "chat" if mode == "chat" else "shot"
    typer.echo(OpenCodeProvider().run_prompt(prompt, tier="code", mode=m))


@opencode_app.command("categorize")
def opencode_categorize_cmd(prompt: str = typer.Argument(..., help="Categorization prompt.")) -> None:
    typer.echo(OpenCodeProvider().run_prompt(prompt, tier="categorize", mode="shot"))


@opencode_app.callback()
def opencode_root(ctx: typer.Context) -> None:
    """Domains: `chat` (planning), `gh` (issues/PRs/review), or raw tier prompts."""
    ctx.ensure_object(dict)
