from __future__ import annotations

from pathlib import Path

import typer

from src.commands._toolkit import dispatch

structure_app = typer.Typer(help="Check repository structure.", no_args_is_help=True)


@structure_app.command("check")
def structure_check_cmd(
    path: Path = typer.Argument(Path("."), help="Repository root."),
    require_layout: bool = typer.Option(False, "--require-layout"),
    require_structure: bool = typer.Option(False, "--require-structure"),
    policy_file: Path | None = typer.Option(None, "--policy-file", help="YAML/JSON language policy file."),
) -> None:
    dispatch(
        "structure",
        "check",
        path,
        extra_env={
            "REQUIRE_LAYOUT": "1" if require_layout else "",
            "REQUIRE_STRUCTURE": "1" if require_structure else "",
            "POLICY_FILE": str(policy_file.expanduser().resolve()) if policy_file else "",
        },
    )

