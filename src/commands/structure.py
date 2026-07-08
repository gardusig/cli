from __future__ import annotations

from pathlib import Path

import typer

from src.commands._toolkit import dispatch
from src.services.workspace_paths import check_workspace_paths

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


@structure_app.command("workspace-paths")
def structure_workspace_paths_cmd(
    manifest: Path = typer.Option(
        Path(".github/required-paths.txt"),
        "--manifest",
        help="Required workspace paths manifest.",
    ),
    workspace_root: Path = typer.Option(
        Path("."),
        "--workspace-root",
        help="Workspace root for full local validation.",
    ),
    base: str | None = typer.Option(
        None,
        "--base",
        help="Validate only manifest entries under this workspace path, mapped to --repo-root.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Checked-out repo root used with --base.",
    ),
) -> None:
    result = check_workspace_paths(
        manifest,
        workspace_root=workspace_root,
        base=base,
        repo_root=repo_root,
    )

    if result.missing:
        typer.echo("::group::Missing required workspace paths")
        for missing in result.missing:
            typer.echo(f"{missing.path} -> {missing.target}")
        typer.echo("::endgroup::")

        for missing in result.missing:
            typer.echo(
                f"::error file={manifest},line={missing.line_number}::"
                f"Required workspace path is missing: {missing.path}",
                err=True,
            )
        raise typer.Exit(1)

    typer.echo(f"workspace paths ok: checked {result.checked}, skipped {result.skipped}")

