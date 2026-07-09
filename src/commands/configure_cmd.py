"""Unified configuration entry point, similar to aws configure / git config."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import typer
import yaml

from src.services.notion_pairs import load_pairs
from src.utils.config import (
    default_config_dir,
    gh_issues_labels_manifest,
    gh_issues_repo,
    load_config,
    notion_pairs_file,
    notion_task_root,
)

configure_app = typer.Typer(help="Configure cli credentials, paths, and defaults.", no_args_is_help=True)

SECRET_KEYS: dict[str, dict[str, str]] = {
    "notion.token": {
        "auth": "notion",
        "env": "NOTION_TOKEN",
        "example": "secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "ci": "github-pipelines/tasks/NOTION_TOKEN",
    },
    "gh.token": {
        "auth": "gh",
        "env": "GH_TOKEN",
        "example": "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "ci": "github-pipelines/tasks/CENTRAL_PIPELINE_PAT",
    },
    "backup.password": {
        "auth": "backup",
        "env": "BACKUP_ZIP_PASSWORD",
        "example": "long random password",
        "ci": "local-only",
    },
    "deepseek.token": {
        "auth": "deepseek",
        "env": "DEEPSEEK_API_KEY",
        "example": "sk-...",
        "ci": "local-only",
    },
    "pypi.token": {
        "auth": "pypi",
        "env": "PYPI_API_TOKEN",
        "example": "pypi-...",
        "ci": "github-pipelines/release/PYPI_API_TOKEN",
    },
}

CONFIG_KEYS: dict[str, dict[str, str]] = {
    "notion.database_id": {"env": "NOTION_DATABASE_ID", "example": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"},
    "notion.task_root": {"env": "NOTION_TASK_ROOT", "example": "/workspace/tasks"},
    "notion.pairs_file": {"env": "", "example": "tasks.pairs.json"},
    "gh.issues.repo": {"env": "", "example": "gardusig/private"},
    "gh.issues.labels_manifest": {"env": "", "example": "labels.manifest.yaml"},
}


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise typer.BadParameter(f"expected mapping in {path}")
    return data


def _nested_set(data: dict[str, Any], dotted: str, value: str) -> None:
    cur: dict[str, Any] = data
    parts = dotted.split(".")
    for part in parts[:-1]:
        nxt = cur.setdefault(part, {})
        if not isinstance(nxt, dict):
            raise typer.BadParameter(f"{'.'.join(parts[:-1])} is not a mapping")
        cur = nxt
    cur[parts[-1]] = value


def _nested_get(data: dict[str, Any], dotted: str) -> Any:
    cur: Any = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _nested_unset(data: dict[str, Any], dotted: str) -> bool:
    cur: Any = data
    parts = dotted.split(".")
    for part in parts[:-1]:
        if not isinstance(cur, dict) or part not in cur:
            return False
        cur = cur[part]
    if isinstance(cur, dict) and parts[-1] in cur:
        del cur[parts[-1]]
        return True
    return False


def _auth_paths(config_dir: Path, key: str) -> tuple[Path, Path, str, str]:
    meta = SECRET_KEYS[key]
    auth_name = meta["auth"]
    token_file = config_dir / "secrets" / f"{auth_name}.token"
    return config_dir / "auth.yaml", token_file, auth_name, meta["env"]


def _set_secret(config_dir: Path, key: str, value: str) -> None:
    auth_path, token_file, auth_name, env_name = _auth_paths(config_dir, key)
    auth = _read_yaml(auth_path)
    auth.setdefault("auth", {})
    auth["auth"][auth_name] = {"env": env_name, "token_file": str(token_file)}
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(value.strip(), encoding="utf-8")
    os.chmod(token_file, 0o600)
    _write_yaml(auth_path, auth)


def _get_secret(config_dir: Path, key: str) -> str | None:
    meta = SECRET_KEYS[key]
    env_value = os.environ.get(meta["env"], "").strip()
    if env_value:
        return env_value
    auth = _read_yaml(config_dir / "auth.yaml")
    token_file = _nested_get(auth, f"auth.{meta['auth']}.token_file")
    if not token_file:
        return None
    path = Path(str(token_file)).expanduser()
    if not path.is_absolute():
        path = config_dir / path
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").strip() or None


def _all_keys() -> list[str]:
    return sorted([*CONFIG_KEYS, *SECRET_KEYS])


@configure_app.callback(invoke_without_command=True)
def configure_root(
    ctx: typer.Context,
    config_dir: Path = typer.Option(default_config_dir(), "--config-dir"),
) -> None:
    """Create config storage when invoked without a subcommand."""
    if ctx.invoked_subcommand is not None:
        return
    config_dir.expanduser().mkdir(parents=True, exist_ok=True)
    typer.echo(f"configuration directory: {config_dir.expanduser()}")
    typer.echo("Run `cli configure list` to inspect available keys.")


@configure_app.command("set")
def set_cmd(
    key: str,
    value: str | None = typer.Argument(None),
    stdin: bool = typer.Option(False, "--stdin", help="Read the value from stdin."),
    config_dir: Path = typer.Option(default_config_dir(), "--config-dir"),
) -> None:
    """Set a dotted config key."""
    if key not in SECRET_KEYS and key not in CONFIG_KEYS:
        raise typer.BadParameter(f"unknown key: {key}")
    if stdin:
        value = sys.stdin.read()
    if value is None:
        raise typer.BadParameter("value is required unless --stdin is used")
    config_dir = config_dir.expanduser()
    if key in SECRET_KEYS:
        _set_secret(config_dir, key, value)
    else:
        config_path = config_dir / "config.yaml"
        data = _read_yaml(config_path)
        _nested_set(data, key, value)
        _write_yaml(config_path, data)
    typer.echo(f"set {key}")


@configure_app.command("get")
def get_cmd(
    key: str,
    show: bool = typer.Option(False, "--show", help="Show secret values instead of masking them."),
    config_dir: Path = typer.Option(default_config_dir(), "--config-dir"),
) -> None:
    """Get a dotted config key."""
    config_dir = config_dir.expanduser()
    if key in SECRET_KEYS:
        value = _get_secret(config_dir, key)
        if not value:
            typer.echo(f"{key} is not set", err=True)
            raise typer.Exit(1)
        typer.echo(value if show else "***")
        return
    data = _read_yaml(config_dir / "config.yaml")
    value = _nested_get(data, key)
    if value is None:
        typer.echo(f"{key} is not set", err=True)
        raise typer.Exit(1)
    typer.echo(value)


@configure_app.command("unset")
def unset_cmd(key: str, config_dir: Path = typer.Option(default_config_dir(), "--config-dir")) -> None:
    """Unset a dotted config key."""
    config_dir = config_dir.expanduser()
    if key in SECRET_KEYS:
        _, token_file, _, _ = _auth_paths(config_dir, key)
        if token_file.exists():
            token_file.unlink()
        typer.echo(f"unset {key}")
        return
    config_path = config_dir / "config.yaml"
    data = _read_yaml(config_path)
    _nested_unset(data, key)
    _write_yaml(config_path, data)
    typer.echo(f"unset {key}")


@configure_app.command("list")
def list_cmd(
    json_output: bool = typer.Option(False, "--json", help="Print JSON."),
    config_dir: Path = typer.Option(default_config_dir(), "--config-dir"),
) -> None:
    """List known configuration keys and whether they are set."""
    rows: list[dict[str, Any]] = []
    config_dir = config_dir.expanduser()
    config_data = _read_yaml(config_dir / "config.yaml")
    for key in _all_keys():
        secret = key in SECRET_KEYS
        meta = SECRET_KEYS.get(key) or CONFIG_KEYS.get(key) or {}
        value = _get_secret(config_dir, key) if secret else _nested_get(config_data, key)
        rows.append(
            {
                "key": key,
                "env": meta.get("env", ""),
                "secret": secret,
                "set": bool(value),
                "value": "***" if secret and value else (value or ""),
                "example": meta.get("example", ""),
                "ci": meta.get("ci", ""),
            }
        )
    if json_output:
        typer.echo(json.dumps(rows, indent=2))
        return
    for row in rows:
        status = "set" if row["set"] else "unset"
        env = f" ({row['env']})" if row["env"] else ""
        typer.echo(f"{row['key']}: {status}{env}")


@configure_app.command("import-env")
def import_env_cmd(
    persist: bool = typer.Option(False, "--persist", help="Persist env values into token files."),
    config_dir: Path = typer.Option(default_config_dir(), "--config-dir"),
) -> None:
    """Validate or persist known credentials from environment variables."""
    imported = 0
    for key, meta in SECRET_KEYS.items():
        value = os.environ.get(meta["env"], "").strip()
        if not value:
            continue
        imported += 1
        if persist:
            _set_secret(config_dir.expanduser(), key, value)
    typer.echo(f"environment credentials available: {imported}")


@configure_app.command("check")
def check_cmd(
    tasks: bool = typer.Option(False, "--tasks"),
    pypi: bool = typer.Option(False, "--pypi"),
) -> None:
    """Validate required configuration for a feature area."""
    missing: list[str] = []
    if tasks:
        root = notion_task_root()
        pairs = notion_pairs_file()
        if not root.is_dir():
            missing.append(f"task root not found: {root}")
        if not pairs.is_file():
            missing.append(f"pairs manifest not found: {pairs}")
        if pairs.is_file():
            load_pairs(pairs, task_root=root)
        labels = gh_issues_labels_manifest()
        if not labels.is_file():
            missing.append(f"labels manifest not found: {labels}")
        gh_issues_repo()
        if not _get_secret(default_config_dir(), "gh.token"):
            missing.append("gh.token is not set; export GH_TOKEN or run cli configure set gh.token")
    if pypi and not _get_secret(default_config_dir(), "pypi.token"):
        missing.append("pypi.token is not set; export PYPI_API_TOKEN or run cli configure set pypi.token")
    if missing:
        typer.echo("\n".join(missing), err=True)
        raise typer.Exit(1)
    typer.echo("configuration ok")
