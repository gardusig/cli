"""Unified registry and runner for every public CLI command in dockerized integration."""

from __future__ import annotations

from pathlib import Path

from cli.cli import app
from cli.integration.cli_api_checks import (
    assert_every_api_command_has_ok_and_fail_check,
    cli_api_checks,
)
from cli.integration.contest_integration import (
    assert_contest_registry_complete,
    assert_every_contest_subcommand_has_ok_and_failure_check,
    contest_checks,
    run_all_contest_checks,
)
from cli.integration.docker_integration import (
    DOCKER_SUBCOMMANDS,
    assert_docker_registry_complete,
    assert_docker_registry_covers_commands,
    assert_every_docker_subcommand_has_ok_and_failure_check,
    docker_checks,
    run_all_docker_checks,
)
from cli.integration.public_endpoints import (
    TOP_LEVEL_COMMANDS,
    assert_every_git_subcommand_checked,
    assert_every_git_subcommand_has_ok_and_failure_check,
    assert_every_top_level_command_checked,
    assert_registry_covers_git_commands,
    endpoint_checks,
    run_all_endpoint_checks,
)
from cli.integration.workspaces import API_WORKSPACES, fixture_dir


def registered_top_level_commands() -> set[str]:
    """Visible Typer groups on the root app (excludes hidden `g` alias)."""
    return {group.name for group in app.registered_groups if not group.hidden}


def assert_top_level_registry_matches_cli() -> None:
    expected = set(TOP_LEVEL_COMMANDS)
    registered = registered_top_level_commands()
    missing = expected - registered
    extra = registered - expected
    if missing or extra:
        raise AssertionError(
            f"top-level command registry drift: missing={sorted(missing)} extra={sorted(extra)}"
        )


def assert_public_command_registry_complete() -> None:
    """Every public top-level group, git subcommand, and docker subcommand has integration checks."""
    assert_top_level_registry_matches_cli()
    assert_registry_covers_git_commands()
    assert_every_git_subcommand_checked()
    assert_every_git_subcommand_has_ok_and_failure_check()
    assert_every_top_level_command_checked()
    assert_docker_registry_covers_commands()
    assert_docker_registry_complete()
    assert_every_docker_subcommand_has_ok_and_failure_check()
    assert_contest_registry_complete()
    assert_every_contest_subcommand_has_ok_and_failure_check()
    gh_ws = fixture_dir(next(w for w in API_WORKSPACES if w.name == "gh"))
    assert_every_api_command_has_ok_and_fail_check(
        cli_api_checks(gh_workspace=gh_ws, drive_repo="."),
    )


def public_command_check_count() -> int:
    return len(endpoint_checks()) + len(docker_checks()) + len(contest_checks())


def run_all_public_command_checks(repo_root: Path, git_root: Path | None = None) -> list[str]:
    from cli.integration.docker_guard import require_docker_integration

    require_docker_integration(context="run_all_public_command_checks")
    """Run dockerized integration for all public commands (endpoints + mocked docker CLI)."""
    assert_public_command_registry_complete()
    errors = run_all_endpoint_checks(repo_root, git_root=git_root)
    errors.extend(run_all_docker_checks(repo_root))
    errors.extend(run_all_contest_checks(repo_root))
    return errors
