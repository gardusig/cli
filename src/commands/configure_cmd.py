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
    bundled_config_dir,
    default_config_dir,
    load_config,
    notion_labels_manifest,
    notion_pairs_file,
    notion_task_root,
    tasks_link_repo,
)

configure_app = typer.Typer(help="Configure cli credentials, paths, and defaults.", no_args_is_help=True)


def _resolve_config_dir(config_dir: Path | None) -> Path:
    return config_dir.expanduser() if config_dir is not None else default_config_dir()

SECRET_KEYS: dict[str, dict[str, str]] = {
    "notion.token": {
        "auth": "notion",
        "env": "NOTION_TOKEN",
        "example": "secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "ci": "github-pipelines/tasks/NOTION_TOKEN",
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
    "docker.token": {
        "auth": "docker",
        "env": "DOCKERHUB_TOKEN",
        "example": "dckr_pat_...",
        "ci": "gardusig/cli/DOCKERHUB_TOKEN",
    },
}

CONFIG_KEYS: dict[str, dict[str, str]] = {
    "backup.tags_dir": {"env": "", "example": "~/git-tags"},
    "chrome.profile": {"env": "", "example": "Default"},
    "chrome.bookmarks_file": {"env": "CLI_BOOKMARKS_FILE", "example": "~/bookmarks/bookmarks.html"},
    "chrome.downloads_dir": {"env": "CLI_DOWNLOADS_DIR", "example": "~/Downloads"},
    "chrome.photos_dir": {"env": "", "example": "~/photos"},
    "chrome.snapshots_dir": {"env": "", "example": "~/bookmarks/snapshots"},
    "docker.username": {"env": "DOCKERHUB_USERNAME", "example": "binaryLifter"},
    "gh.issues.repo": {"env": "", "example": "owner/repo"},
    "notion.database_id": {"env": "NOTION_DATABASE_ID", "example": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"},
    "notion.task_root": {"env": "NOTION_TASK_ROOT", "example": "~/github/private/tasks"},
    "notion.pairs_file": {"env": "", "example": "tasks.pairs.json"},
    "notion.link_repo": {"env": "", "example": "gardusig/private"},
    "notion.labels_manifest": {"env": "", "example": "labels.manifest.yaml"},
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
    if auth_name == "backup":
        rel = Path("secrets") / "backup.zip.password"
    else:
        rel = Path("secrets") / f"{auth_name}.token"
    return config_dir / "auth.yaml", config_dir / rel, auth_name, meta["env"]


def _set_secret(config_dir: Path, key: str, value: str) -> None:
    auth_path, token_file, auth_name, env_name = _auth_paths(config_dir, key)
    rel = token_file.relative_to(config_dir)
    auth = _read_yaml(auth_path)
    auth.setdefault("auth", {})
    auth["auth"][auth_name] = {"env": env_name, "token_file": str(rel)}
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


def _config_value(config_dir: Path, key: str) -> Any:
    data = _read_yaml(config_dir / "config.yaml")
    value = _nested_get(data, key)
    if value is not None:
        return value
    meta = CONFIG_KEYS.get(key) or {}
    env_name = meta.get("env", "").strip()
    if env_name:
        env_value = os.environ.get(env_name, "").strip()
        if env_value:
            return env_value
    return None


def _all_keys() -> list[str]:
    return sorted([*CONFIG_KEYS, *SECRET_KEYS])


def _init_auth_layout(config_dir: Path) -> None:
    """Create secrets/ and auth.yaml (git-style credential store)."""
    secret_dir = config_dir / "secrets"
    secret_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(secret_dir, 0o700)
    auth: dict[str, Any] = {"auth": {}}
    for key, meta in SECRET_KEYS.items():
        auth_name = meta["auth"]
        token_file = Path("secrets") / f"{auth_name}.token"
        if auth_name == "backup":
            token_file = Path("secrets") / "backup.zip.password"
        auth["auth"][auth_name] = {"env": meta["env"], "token_file": str(token_file)}
        path = config_dir / token_file
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
            os.chmod(path, 0o600)
    _write_yaml(config_dir / "auth.yaml", auth)


@configure_app.command("init")
def init_cmd(
    example: bool = typer.Option(
        False,
        "--example",
        help="Also write config.example.yaml as config.yaml (paths only; edit before use).",
    ),
    config_dir: Path | None = typer.Option(None, "--config-dir"),
) -> None:
    """Bootstrap the user config directory (like aws configure / git config --global)."""
    config_dir = _resolve_config_dir(config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)
    _init_auth_layout(config_dir)
    config_file = config_dir / "config.yaml"
    if example and not config_file.exists():
        template = bundled_config_dir() / "config.example.yaml"
        if template.is_file():
            config_file.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            typer.echo(f"example template missing: {template}", err=True)
            raise typer.Exit(1)
    typer.echo(f"configuration directory: {config_dir}")
    typer.echo("Secrets layout: auth.yaml + secrets/")
    typer.echo("Set paths and tokens with `cli configure set <key> [value]` or `--stdin`.")
    typer.echo("Run `cli configure list` to see available keys.")


@configure_app.command("path")
def path_cmd(config_dir: Path | None = typer.Option(None, "--config-dir")) -> None:
    """Print the active configuration directory."""
    typer.echo(str(_resolve_config_dir(config_dir)))


@configure_app.callback(invoke_without_command=True)
def configure_root(
    ctx: typer.Context,
    config_dir: Path | None = typer.Option(None, "--config-dir"),
) -> None:
    """Without a subcommand, bootstrap storage and print the config directory."""
    if ctx.invoked_subcommand is not None:
        return
    init_cmd(example=False, config_dir=config_dir)


@configure_app.command("set")
def set_cmd(
    key: str,
    value: str | None = typer.Argument(None),
    stdin: bool = typer.Option(False, "--stdin", help="Read the value from stdin."),
    config_dir: Path | None = typer.Option(None, "--config-dir"),
) -> None:
    """Set a dotted config key."""
    if key not in SECRET_KEYS and key not in CONFIG_KEYS:
        raise typer.BadParameter(f"unknown key: {key}")
    if stdin:
        value = sys.stdin.read()
    if value is None:
        raise typer.BadParameter("value is required unless --stdin is used")
    config_dir = _resolve_config_dir(config_dir)
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
    config_dir: Path | None = typer.Option(None, "--config-dir"),
) -> None:
    """Get a dotted config key."""
    config_dir = _resolve_config_dir(config_dir)
    if key in SECRET_KEYS:
        value = _get_secret(config_dir, key)
        if not value:
            typer.echo(f"{key} is not set", err=True)
            raise typer.Exit(1)
        typer.echo(value if show else "***")
        return
    value = _config_value(config_dir, key)
    if value is None:
        typer.echo(f"{key} is not set", err=True)
        raise typer.Exit(1)
    typer.echo(value)


@configure_app.command("unset")
def unset_cmd(key: str, config_dir: Path | None = typer.Option(None, "--config-dir")) -> None:
    """Unset a dotted config key."""
    config_dir = _resolve_config_dir(config_dir)
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
    config_dir: Path | None = typer.Option(None, "--config-dir"),
) -> None:
    """List known configuration keys and whether they are set."""
    rows: list[dict[str, Any]] = []
    config_dir = _resolve_config_dir(config_dir)
    for key in _all_keys():
        secret = key in SECRET_KEYS
        meta = SECRET_KEYS.get(key) or CONFIG_KEYS.get(key) or {}
        value = _get_secret(config_dir, key) if secret else _config_value(config_dir, key)
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
    config_dir: Path | None = typer.Option(None, "--config-dir"),
) -> None:
    """Validate or persist known credentials from environment variables."""
    imported = 0
    for key, meta in SECRET_KEYS.items():
        value = os.environ.get(meta["env"], "").strip()
        if not value:
            continue
        imported += 1
        if persist:
            _set_secret(_resolve_config_dir(config_dir), key, value)
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
        labels = notion_labels_manifest()
        if not labels.is_file():
            missing.append(f"labels manifest not found: {labels}")
        tasks_link_repo()
    if pypi and not _get_secret(default_config_dir(), "pypi.token"):
        missing.append("pypi.token is not set; export PYPI_API_TOKEN or run cli configure set pypi.token")
    if missing:
        typer.echo("\n".join(missing), err=True)
        raise typer.Exit(1)
    typer.echo("configuration ok")
