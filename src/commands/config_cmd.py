"""Configuration setup and diagnostics."""

from __future__ import annotations

import json
import os
from pathlib import Path

import typer
import yaml

from src.commands.configure_cmd import (
    check_cmd as configure_check_cmd,
    import_env_cmd as configure_import_env_cmd,
    list_cmd as configure_list_cmd,
    set_cmd as configure_set_cmd,
)
from src.utils.config import default_config_dir, load_config

config_app = typer.Typer(help="Configure cli paths and secrets.", no_args_is_help=True)
secrets_app = typer.Typer(help="Secret setup helpers.", no_args_is_help=True)
config_app.add_typer(secrets_app, name="secrets")


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


@config_app.command("init")
def init_cmd(
    config_dir: Path = typer.Option(default_config_dir(), "--config-dir"),
) -> None:
    """Create a starter config directory if missing."""
    config_dir = config_dir.expanduser()
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.yaml"
    if not config_file.exists():
        _write_yaml(
            config_file,
            {
                "notion": {
                    "database_id": "your-notion-database-id",
                    "task_root": "~/github/private/database/tasks",
                    "pairs_file": "tasks.pairs.json",
                },
                "gh": {
                    "issues": {
                        "repo": "gardusig/database",
                        "labels_manifest": "labels.manifest.yaml",
                    }
                },
            },
        )
    typer.echo(f"initialized {config_dir}")


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
def set_cmd(key: str, value: str, config_dir: Path = typer.Option(default_config_dir(), "--config-dir")) -> None:
    """Set a dotted key in config.yaml."""
    typer.echo("cli config set is deprecated; use cli configure set")
    configure_set_cmd(key=key, value=value, stdin=False, config_dir=config_dir)


@secrets_app.command("init")
def secrets_init_cmd(config_dir: Path = typer.Option(default_config_dir(), "--config-dir")) -> None:
    """Create local token-file placeholders and auth.yaml."""
    config_dir = config_dir.expanduser()
    secret_dir = config_dir / "secrets"
    secret_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(secret_dir, 0o700)
    auth = {
        "auth": {
            "notion": {"env": "NOTION_TOKEN", "token_file": str(secret_dir / "notion.token")},
            "gh": {"env": "GH_TOKEN", "token_file": str(secret_dir / "github.token")},
            "backup": {
                "env": "BACKUP_ZIP_PASSWORD",
                "token_file": str(secret_dir / "backup.zip.password"),
            },
            "deepseek": {"env": "DEEPSEEK_API_KEY", "token_file": str(secret_dir / "deepseek.token")},
            "pypi": {"env": "PYPI_API_TOKEN", "token_file": str(secret_dir / "pypi.token")},
        }
    }
    for item in auth["auth"].values():
        p = Path(item["token_file"])
        if not p.exists():
            p.write_text("", encoding="utf-8")
            os.chmod(p, 0o600)
    _write_yaml(config_dir / "auth.yaml", auth)
    typer.echo(f"initialized secrets in {secret_dir}")


@secrets_app.command("list")
def secrets_list_cmd() -> None:
    """List expected secret names, without values."""
    typer.echo("cli config secrets list is deprecated; use cli configure list")
    configure_list_cmd(json_output=True, config_dir=default_config_dir())


@secrets_app.command("import-env")
def secrets_import_env_cmd(
    persist: bool = typer.Option(False, "--persist"),
    config_dir: Path = typer.Option(default_config_dir(), "--config-dir"),
) -> None:
    """Deprecated alias for cli configure import-env."""
    typer.echo("cli config secrets import-env is deprecated; use cli configure import-env")
    configure_import_env_cmd(persist=persist, config_dir=config_dir)
