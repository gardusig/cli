"""cli configure — aws/git-style user config bootstrap."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.cli import app
from src.utils.config import default_config_dir, user_cli_config_dir

runner = CliRunner()


def test_user_cli_config_dir_uses_platformdirs() -> None:
    path = user_cli_config_dir()
    assert path.is_absolute()
    assert path.name == "cli"


def test_default_config_dir_without_override_uses_user_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLI_CONFIG_DIR", raising=False)
    assert default_config_dir() == user_cli_config_dir()


def test_configure_init_creates_auth_layout(tmp_path: Path) -> None:
    result = runner.invoke(app, ["configure", "init", "--config-dir", str(tmp_path)])
    assert result.exit_code == 0, result.stdout + (result.stderr or "")
    assert (tmp_path / "auth.yaml").is_file()
    assert (tmp_path / "secrets").is_dir()
    assert (tmp_path / "secrets" / "notion.token").is_file()
    assert (tmp_path / "config.yaml").exists() is False


def test_configure_set_and_get_roundtrip(tmp_path: Path) -> None:
    runner.invoke(app, ["configure", "init", "--config-dir", str(tmp_path)])
    set_result = runner.invoke(
        app,
        ["configure", "set", "notion.task_root", "/tmp/tasks", "--config-dir", str(tmp_path)],
    )
    assert set_result.exit_code == 0, set_result.stdout
    get_result = runner.invoke(
        app,
        ["configure", "get", "notion.task_root", "--config-dir", str(tmp_path)],
    )
    assert get_result.exit_code == 0
    assert get_result.stdout.strip() == "/tmp/tasks"


def test_configure_path_prints_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLI_CONFIG_DIR", str(tmp_path))
    result = runner.invoke(app, ["configure", "path"])
    assert result.exit_code == 0
    assert result.stdout.strip() == str(tmp_path)


def test_fresh_load_config_uses_code_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("CLI_PROFILE", raising=False)
    from src.utils.config import load_config

    cfg = load_config()
    assert cfg.backup.tags_dir == ""
    assert cfg.backup.repositories == []
    assert cfg.notion.database_id == ""
