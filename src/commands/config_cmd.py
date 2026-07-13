"""Configuration setup and diagnostics."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from src.commands.configure_cmd import (
    check_cmd as configure_check_cmd,
    import_env_cmd as configure_import_env_cmd,
    init_cmd as configure_init_cmd,
    list_cmd as configure_list_cmd,
    set_cmd as configure_set_cmd,
)
from src.utils.config import default_config_dir, load_config

config_app = typer.Typer(help="Configure cli paths and secrets.", no_args_is_help=True)
secrets_app = typer.Typer(help="Secret setup helpers.", no_args_is_help=True)
config_app.add_typer(secrets_app, name="secrets")


@config_app.command("init")
def init_cmd(
    config_dir: Path | None = typer.Option(None, "--config-dir"),
) -> None:
    """Deprecated alias for cli configure init."""
    typer.echo("cli config init is deprecated; use cli configure init")
    configure_init_cmd(example=False, config_dir=config_dir)


@config_app.command("show")
def show_cmd() -> None:
    """Print resolved non-secret config."""
    cfg = load_config()
    data = cfg.model_dump()
    data.pop("auth", None)
    typer.echo(json.dumps(data, indent=2))


@config_app.command("check")
def check_cmd(tasks: bool = typer.Option(False, "--tasks")) -> None:
    """Validate paths and required credentials for configured features."""
    typer.echo("cli config check is deprecated; use cli configure check")
    configure_check_cmd(tasks=tasks, pypi=False)


@config_app.command("set")
def set_cmd(
    key: str,
    value: str,
    config_dir: Path | None = typer.Option(None, "--config-dir"),
) -> None:
    """Set a dotted key in config.yaml."""
    typer.echo("cli config set is deprecated; use cli configure set")
    configure_set_cmd(key=key, value=value, stdin=False, config_dir=config_dir)


@secrets_app.command("init")
def secrets_init_cmd(config_dir: Path | None = typer.Option(None, "--config-dir")) -> None:
    """Deprecated alias for cli configure init."""
    typer.echo("cli config secrets init is deprecated; use cli configure init")
    configure_init_cmd(example=False, config_dir=config_dir)


@secrets_app.command("list")
def secrets_list_cmd() -> None:
    """List expected secret names, without values."""
    typer.echo("cli config secrets list is deprecated; use cli configure list")
    configure_list_cmd(json_output=True, config_dir=default_config_dir())


@secrets_app.command("import-env")
def secrets_import_env_cmd(
    persist: bool = typer.Option(False, "--persist"),
    config_dir: Path | None = typer.Option(None, "--config-dir"),
) -> None:
    """Deprecated alias for cli configure import-env."""
    typer.echo("cli config secrets import-env is deprecated; use cli configure import-env")
    configure_import_env_cmd(persist=persist, config_dir=config_dir)
