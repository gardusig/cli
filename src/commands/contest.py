"""Competitive programming validation."""

from __future__ import annotations

from pathlib import Path

import typer
from rich import print as rprint
from rich.table import Table

from src.services.contest_docker import RunStatus
from src.services.contest_runner import (
    ContestValidateResult,
    resolve_options,
    validate_contest,
)

contest_app = typer.Typer(
    help="Competitive programming validation (generator, brute, fast).",
    no_args_is_help=True,
)


def _status_style(status: RunStatus) -> str:
    if status == RunStatus.OK:
        return "green"
    if status == RunStatus.TLE:
        return "yellow"
    return "red"


def _print_outcome_row(
    table: Table,
    tier: str,
    role: str,
    outcome,
) -> None:
    table.add_row(
        tier,
        role,
        f"[{_status_style(outcome.status)}]{outcome.status.value}[/]",
        f"{outcome.seconds:.2f}s",
    )


def _print_result(result: ContestValidateResult) -> None:
    if result.error and result.small is None and result.large is None:
        rprint(f"[red]error:[/red] {result.error}")
        rprint("[red]FAIL[/red]")
        return

    table = Table(title="Contest validate", show_header=True, header_style="bold")
    table.add_column("Tier")
    table.add_column("Role")
    table.add_column("Status")
    table.add_column("Time", justify="right")

    if result.small:
        _print_outcome_row(table, "small", "brute", result.small.brute)
        _print_outcome_row(table, "small", "fast", result.small.fast)
        match = result.small.outputs_match
        if match is not None:
            style = "green" if match else "red"
            table.add_row(
                "small",
                "compare",
                f"[{style}]{'match' if match else 'mismatch'}[/]",
                "",
            )

    if result.large:
        _print_outcome_row(table, "large", "brute", result.large.brute)
        _print_outcome_row(table, "large", "fast", result.large.fast)

    rprint(table)

    if result.small_diff:
        rprint("\n[red]small tier diff:[/red]")
        rprint(result.small_diff)

    for warning in result.warnings:
        rprint(f"[yellow]warning:[/yellow] {warning}")

    if result.error:
        rprint(f"[red]error:[/red] {result.error}")

    if result.passed:
        rprint("[green]PASS[/green]")
    else:
        rprint("[red]FAIL[/red]")


@contest_app.command("validate")
def validate_cmd(
    fast: Path | None = typer.Option(None, "--fast", help="Path to fast C++ solution."),
    brute: Path | None = typer.Option(None, "--brute", help="Path to Python brute solution."),
    generator: Path | None = typer.Option(None, "--generator", help="Path to Python input generator."),
    config: Path | None = typer.Option(None, "--config", help="Optional YAML config with paths and limits."),
    timeout: float | None = typer.Option(None, "--timeout", help="Per-container time limit in seconds."),
    memory_mb: int | None = typer.Option(None, "--memory-mb", help="Per-container memory limit in MB."),
    image: str | None = typer.Option(None, "--image", help="Docker image for solution runs."),
    cxx_std: str | None = typer.Option(None, "--cxx-std", help="C++ standard passed to g++, e.g. c++17."),
) -> None:
    """Validate fast C++ vs brute Python on small (compare) and large (stress) tiers."""
    try:
        options = resolve_options(
            fast=fast,
            brute=brute,
            generator=generator,
            config=config,
            timeout=timeout,
            memory_mb=memory_mb,
            image=image,
            cxx_std=cxx_std,
        )
    except (ValueError, FileNotFoundError) as exc:
        rprint(f"[red]error:[/red] {exc}")
        raise typer.Exit(1) from exc

    result = validate_contest(options)
    _print_result(result)
    raise typer.Exit(0 if result.passed else 1)
