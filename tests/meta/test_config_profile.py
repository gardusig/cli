"""Config profile merge and resolution."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.utils.config import active_config_profile, load_config


def test_active_config_profile_from_cli_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLI_PROFILE", "test")
    monkeypatch.delenv("CLI_ENV", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    assert active_config_profile() == "test"


def test_active_config_profile_from_cli_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLI_PROFILE", raising=False)
    monkeypatch.setenv("CLI_ENV", "test")
    assert active_config_profile() == "test"


def test_active_config_profile_from_pytest(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLI_PROFILE", raising=False)
    monkeypatch.delenv("CLI_ENV", raising=False)
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "tests/meta/test_config_profile.py::test")
    assert active_config_profile() == "test"


def test_load_config_merges_test_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text(
        "backup:\n  tags_dir: base-tags\nnotion:\n  database_id: base-db\n",
        encoding="utf-8",
    )
    (cfg_dir / "config.test.yaml").write_text(
        "backup:\n  tags_dir: test-tags\nnotion:\n  task_root: tests/fixtures/notion/tasks\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("CLI_CONFIG_DIR", raising=False)
    monkeypatch.setenv("CLI_PROFILE", "test")

    cfg = load_config(cfg_dir)
    assert cfg.backup.tags_dir == "test-tags"
    assert cfg.notion.database_id == "base-db"
    assert cfg.notion.task_root == "tests/fixtures/notion/tasks"


def test_explicit_config_dir_skips_profile_merge(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text("backup:\n  tags_dir: base-tags\n", encoding="utf-8")
    (cfg_dir / "config.test.yaml").write_text("backup:\n  tags_dir: test-tags\n", encoding="utf-8")
    monkeypatch.setenv("CLI_CONFIG_DIR", str(cfg_dir))
    monkeypatch.setenv("CLI_PROFILE", "test")

    cfg = load_config()
    assert cfg.backup.tags_dir == "base-tags"


def test_repo_test_profile_uses_fixture_paths() -> None:
    from tests.constants import ROOT

    cfg = load_config(ROOT / "config")
    assert cfg.notion.task_root == "tests/fixtures/notion/tasks"
    assert cfg.chrome.bookmarks_file == "tests/fixtures/bookmarks.html"
