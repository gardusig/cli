"""Deploy command."""

from __future__ import annotations

import typer

from src.internal.write.gate import require_write_gate

deploy_app = typer.Typer(help="Deploy (tag main on push).", no_args_is_help=True)


@deploy_app.callback(invoke_without_command=True)
def deploy_cmd(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip write gate."),
) -> None:
    require_write_gate("deploy", ["repo: local"], yes=yes)
    typer.echo("Use `cli pypi upload --yes` for gardusig-cli releases.")
