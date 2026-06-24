from __future__ import annotations

import typer
from rich import print as rprint

from src.utils.catalog import (
    QUICK_DEFAULTS,
    QUICK_DEFAULT_SCRIPTS,
    TOP_LEVEL_COMMANDS,
    WORKFLOW_CHAIN,
    WORKFLOW_SHORTCUTS,
    chrome_script_entries,
    doc_entries,
    git_script_entries,
)
from src.utils.config import project_root

links_app = typer.Typer(help="Index of docs, scripts, and quick defaults.", invoke_without_command=True)


@links_app.callback(invoke_without_command=True)
def links_root() -> None:
    """Print full cli index (docs, scripts, defaults)."""
    root = project_root()
    rprint("[bold]cli index[/bold]")
    rprint(f"repo: {root}\n")

    rprint("[bold]Workflow lifecycle[/bold]")
    rprint(f"  {WORKFLOW_CHAIN}")
    for cli_cmd, script, doc, note in WORKFLOW_SHORTCUTS:
        rprint(
            f"  [cyan]cli {cli_cmd}[/cyan] — {note}"
            f"\n    [dim]scripts/git/{script} · {doc}[/dim]"
        )

    rprint("\n[bold]Quick defaults[/bold] (pass [cyan]--yes[/cyan] / [cyan]-y[/cyan] to skip write gates)")
    for cmd, note in QUICK_DEFAULTS:
        script = QUICK_DEFAULT_SCRIPTS.get(cmd)
        suffix = f" · [dim]{script}[/dim]" if script else ""
        rprint(f"  [cyan]cli {cmd}[/cyan] — {note}{suffix}")
    rprint("  [dim]docs/workflows.md · docs/quick-defaults.md · docs/large-files.md[/dim]")

    rprint("\n[bold]Top-level commands[/bold]")
    for name, desc in TOP_LEVEL_COMMANDS:
        rprint(f"  [cyan]cli {name}[/cyan] — {desc}")

    rprint("\n[bold]Documentation[/bold]")
    for entry in doc_entries(root):
        rprint(f"  {entry.doc}")

    rprint("\n[bold]Git scripts[/bold] → [dim]scripts/git/[/dim] (see docs/git.md)")
    for entry in git_script_entries(root):
        line = f"  {entry.script} → {entry.cli}"
        if entry.label == "large files":
            line += " — [dim]docs/large-files.md[/dim]"
        rprint(line)

    rprint("\n[bold]Chrome scripts[/bold] → [dim]scripts/chrome/[/dim] (see docs/bookmarks.md)")
    for entry in chrome_script_entries(root):
        rprint(f"  {entry.script} — {entry.note}")

    rprint("\n[bold]PyPI scripts[/bold] → [dim]scripts/pypi/[/dim]")
    for rel, note in (
        ("scripts/pypi/install.sh", "install cli from PyPI → ~/.local/bin"),
        ("scripts/pypi/test.sh", "PR gate: build 1.0.0 + optional TestPyPI upload"),
        ("scripts/pypi/release.sh", "PyPI release (Docker cli:release; local + CI)"),
        ("scripts/pypi/publish.sh", "in-container: version resolve → upload"),
        ("scripts/pypi/build.sh", "build sdist + wheel (dist/)"),
        ("scripts/pypi/upload.sh", "upload to PyPI (PYPI_API_TOKEN)"),
    ):
        path = root / rel
        if path.is_file():
            rprint(f"  {rel} — {note}")

    rprint("\n[bold]Other scripts[/bold]")
    for rel, note in (
        ("scripts/docker/build-images.sh", "build all Docker stages"),
        ("scripts/docker/build-image.sh", "build one Docker stage"),
        ("scripts/docker/build-contest-image.sh", "build cli-contest:runner image"),
        ("scripts/test/unit.sh", "unit tests in container"),
        ("scripts/test/integration.sh", "integration tests in container"),
        ("scripts/test/smoke.sh", "integration smoke (container only)"),
        ("scripts/docker/shell.sh", "onboard shell in container"),
        ("scripts/drive/status.sh", "git-tags backup status"),
        ("scripts/gh/sync-labels.sh", "sync label manifest to GitHub"),
    ):
        path = root / rel
        if path.is_file():
            rprint(f"  {rel} — {note}")

    rprint("\n[dim]Tip: cli git docs lists markdown paths for @git-docs[/dim]")
