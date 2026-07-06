from __future__ import annotations

from pathlib import Path

import typer

from src.services.toolkit.detect import ToolkitDetectionError
from src.services.toolkit.prereqs import ToolkitPrereqError
from src.services.toolkit.runner import run_cli_command


def dispatch(
    group: str,
    subject: str,
    path: Path,
    *,
    suite: str | None = None,
    extra_env: dict[str, str] | None = None,
) -> None:
    try:
        code = run_cli_command(group, subject, path, suite=suite, extra_env=extra_env)
    except (FileNotFoundError, KeyError, ToolkitDetectionError, ToolkitPrereqError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    except SystemExit as exc:
        if exc.code and not isinstance(exc.code, int):
            typer.echo(str(exc.code), err=True)
            raise typer.Exit(1) from exc
        raise typer.Exit(exc.code or 0) from exc
    if code != 0:
        raise typer.Exit(code)

