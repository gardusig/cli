"""Repo-agnostic planning chat — DeepSeek only."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import typer

from src.internal.write.gate import require_write_gate
from src.providers.deepseek import DeepSeekClient
from src.services.chat_distill import (
    apply_categorize_plan,
    pipeline_from_summary,
    run_categorize,
    run_r1_distill,
)
from src.services.chat_session import ChatSession, chat_root

chat_app = typer.Typer(
    help="High-level planning chat (no repo attachment). DeepSeek chat / R1 / categorize.",
    no_args_is_help=True,
)

_current_session: str | None = None


def _session_file() -> Path:
    return chat_root() / "current-session"


def _resolve_session(session: str | None) -> ChatSession:
    sid = session
    if not sid and _current_session:
        sid = _current_session
    if not sid and _session_file().is_file():
        sid = _session_file().read_text(encoding="utf-8").strip()
    if not sid:
        raise typer.BadParameter("No session — run: cli chat start")
    return ChatSession.load(sid)


def _set_current(session_id: str) -> None:
    global _current_session
    _current_session = session_id
    chat_root().mkdir(parents=True, exist_ok=True)
    _session_file().write_text(session_id + "\n", encoding="utf-8")


@chat_app.command("start")
def chat_start_cmd(
    session: str | None = typer.Option(None, "--session", "-s", help="Session id (auto if omitted)."),
) -> None:
    s = ChatSession.create(session)
    _set_current(s.session_id)
    typer.echo(json.dumps({"session_id": s.session_id, "dir": str(s.dir)}, indent=2))


@chat_app.command("list")
def chat_list_cmd() -> None:
    typer.echo(json.dumps({"sessions": ChatSession.list_sessions()}, indent=2))


@chat_app.command("send")
def chat_send_cmd(
    message: str = typer.Argument(..., help="User message."),
    session: str | None = typer.Option(None, "--session", "-s"),
) -> None:
    s = _resolve_session(session)
    client = DeepSeekClient()
    if not client.available():
        typer.echo("WARN: DEEPSEEK_API_KEY not set — stub responses only.", err=True)
    reply = s.reply(message, client)
    typer.echo(reply)


@chat_app.command("show")
def chat_show_cmd(
    session: str | None = typer.Option(None, "--session", "-s"),
    format: str = typer.Option("text", "--format", help="text or json"),
) -> None:
    s = _resolve_session(session)
    if format == "json":
        typer.echo(json.dumps(s.export_bundle(), indent=2))
        return
    typer.echo(f"# session {s.session_id}\n")
    if s.summary():
        typer.echo("## Summary\n" + s.summary())
    typer.echo("\n## Transcript\n" + s.transcript_text())


@chat_app.command("summary")
def chat_summary_cmd(
    session: str | None = typer.Option(None, "--session", "-s"),
    refresh: bool = typer.Option(True, "--refresh/--no-refresh"),
) -> None:
    s = _resolve_session(session)
    text = s.refresh_summary() if refresh else s.summary()
    typer.echo(text)


@chat_app.command("distill")
def chat_distill_cmd(
    session: str | None = typer.Option(None, "--session", "-s"),
) -> None:
    """R1 / reasoner — extensive traversal of chat ideas."""
    s = _resolve_session(session)
    data = run_r1_distill(s)
    typer.echo(json.dumps(data, indent=2))


@chat_app.command("categorize")
def chat_categorize_cmd(
    session: str | None = typer.Option(None, "--session", "-s"),
) -> None:
    """R4-class model — parent issue per repo + comment/create actions."""
    s = _resolve_session(session)
    data = run_categorize(s)
    typer.echo(json.dumps(data, indent=2))


@chat_app.command("issues")
def chat_issues_cmd(
    session: str | None = typer.Option(None, "--session", "-s"),
    from_file: Path | None = typer.Option(None, "--from-file", help="Import summary text (workflow)."),
    skip_distill: bool = typer.Option(False, "--skip-distill"),
    apply: bool = typer.Option(False, "--apply", help="Create/comment on GitHub."),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Full pipeline: optional R1 distill → categorize → dry-run or apply."""
    plan: dict[str, Any]
    if from_file:
        summary = from_file.read_text(encoding="utf-8")
        result = pipeline_from_summary(summary, run_distill=not skip_distill)
        plan = result["plan"]
        typer.echo(json.dumps(result, indent=2))
    else:
        s = _resolve_session(session)
        if not skip_distill:
            run_r1_distill(s)
        plan = run_categorize(s)
        typer.echo(json.dumps(plan, indent=2))

    if apply:
        require_write_gate(
            "chat-issues-apply",
            [f"repos: {len(plan.get('repos', []))}"],
            yes=yes,
        )
        applied = apply_categorize_plan(plan, yes=yes)
        typer.echo(json.dumps({"applied": applied}, indent=2))


@chat_app.command("read")
def chat_read_cmd() -> None:
    """Read one user line from stdin (for interactive / workflow use)."""
    line = sys.stdin.readline()
    if not line:
        raise typer.Exit(0)
    chat_send_cmd(line.rstrip("\n"), session=None)


@chat_app.callback()
def chat_root_cb(
    ctx: typer.Context,
    session: str | None = typer.Option(None, "--session", "-s", help="Default session id."),
) -> None:
    ctx.ensure_object(dict)
    if session:
        ctx.obj["session"] = session
