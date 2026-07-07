from __future__ import annotations

import typer
from rich import print as rprint

from src.utils.catalog import (
    QUICK_DEFAULTS,
    TOP_LEVEL_COMMANDS,
    WORKFLOW_CHAIN,
    WORKFLOW_SHORTCUTS,
    chrome_command_entries,
    doc_entries,
    gh_command_entries,
    git_command_entries,
)
from src.utils.config import project_root

links_app = typer.Typer(help="Index of docs, commands, and quick defaults.", invoke_without_command=True)


@links_app.callback(invoke_without_command=True)
def links_root() -> None:
    """Print full cli index (docs, commands, defaults)."""
    root = project_root()
    rprint("[bold]cli index[/bold]")
    rprint(f"repo: {root}\n")

    rprint("[bold]Workflow lifecycle[/bold]")
    rprint(f"  {WORKFLOW_CHAIN}")
    for cli_cmd, doc, note in WORKFLOW_SHORTCUTS:
        rprint(f"  [cyan]cli {cli_cmd}[/cyan] — {note}\n    [dim]{doc}[/dim]")

    rprint("\n[bold]Quick defaults[/bold] (pass [cyan]--yes[/cyan] / [cyan]-y[/cyan] to skip write gates)")
    for cmd, note in QUICK_DEFAULTS:
        rprint(f"  [cyan]cli {cmd}[/cyan] — {note}")
    rprint("  [dim]docs/workflows.md · docs/quick-defaults.md · docs/large-files.md[/dim]")

    rprint("\n[bold]Top-level commands[/bold]")
    for name, desc in TOP_LEVEL_COMMANDS:
        rprint(f"  [cyan]cli {name}[/cyan] — {desc}")

    rprint("\n[bold]Documentation[/bold]")
    for entry in doc_entries(root):
        rprint(f"  {entry.doc}")

    rprint("\n[bold]Git commands[/bold] (see docs/git.md)")
    for entry in git_command_entries(root):
        line = f"  {entry.cli}"
        if entry.label == "large files":
            line += " — [dim]docs/large-files.md[/dim]"
        rprint(line)

    rprint("\n[bold]GitHub commands[/bold] (see docs/gh.md)")
    for entry in gh_command_entries(root):
        rprint(f"  {entry.cli}")

    rprint("\n[bold]Chrome commands[/bold] (see docs/bookmarks.md)")
    for entry in chrome_command_entries(root):
        rprint(f"  {entry.cli} — {entry.note}")

    rprint("\n[bold]Install and release[/bold]")
    rprint("  pip install gardusig-cli — install the published CLI")
    rprint("  cli configure list — inspect configuration keys")
    rprint("  cli pypi build — build sdist + wheel")
    rprint("  cli pypi upload --yes — publish to PyPI")

    rprint("\n[bold]Pipeline commands[/bold]")
    rprint("  cli test python unit — unit gate")
    rprint("  cli test python integration — integration gate")
    rprint("  cli structure check PATH --require-layout — repo structure")
    rprint("  cli repo inventory gardusig/cli — repository snapshot")

    rprint("\n[dim]Tip: cli git docs lists markdown paths for @git-docs[/dim]")
