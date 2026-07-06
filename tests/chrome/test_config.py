"""Chrome config path resolution tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.utils.config import bookmarks_file_path, chrome_profile_key, load_config


def test_bookmarks_file_path_missing_raises(tmp_path: Path, monkeypatch) -> None:
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text("chrome:\n  bookmarks_file: ''\n", encoding="utf-8")
    monkeypatch.delenv("CLI_BOOKMARKS_FILE", raising=False)
    monkeypatch.setenv("CLI_CONFIG_DIR", str(cfg_dir))
    with pytest.raises(FileNotFoundError, match="bookmarks_file"):
        bookmarks_file_path()


def test_bookmarks_file_path_profile_map(tmp_path: Path, monkeypatch) -> None:
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    work_file = tmp_path / "bookmarks-work.html"
    (cfg_dir / "config.yaml").write_text(
        "chrome:\n"
        "  profile: Default\n"
        "  bookmarks_file: bookmarks-default.html\n"
        "  profiles:\n"
        "    Work:\n"
        f"      bookmarks_file: {work_file}\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("CLI_BOOKMARKS_FILE", raising=False)
    monkeypatch.setenv("CLI_CONFIG_DIR", str(cfg_dir))
    assert bookmarks_file_path("Work") == work_file.resolve()


def test_chrome_profile_key_defaults_to_config() -> None:
    cfg = load_config()
    assert chrome_profile_key(None) == (cfg.chrome.profile.strip() or "Default")
