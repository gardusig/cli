"""Unit tests for cli.utils helpers."""

from __future__ import annotations

from tests.constants import ROOT

import subprocess
from pathlib import Path

import pytest
import yaml

from src.utils import fs, hashing, retry, zip as zip_util
from src.providers.notion import NotionError
from src.utils.confirm import require_confirmation
from src.utils.config import default_config_dir, load_config, load_yaml, project_root
from src.utils.external_client import ExternalCallError
from src.utils.process import GitCommandError, run_git
from src.utils.yaml import dump_yaml, load_yaml as utils_load_yaml


def test_project_root_points_at_repo() -> None:
    root = project_root()
    assert (root / "pyproject.toml").is_file()


def test_project_root_respects_cli_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CLI_ROOT", str(tmp_path))
    assert project_root() == tmp_path.resolve()


def test_tags_dir_path_resolves_icloud_absolute(tmp_path: Path) -> None:
    icloud = tmp_path / "Mobile Documents" / "com~apple~CloudDocs" / "git-tags"
    icloud.mkdir(parents=True)
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text(
        f"backup:\n  tags_dir: {icloud}\n",
        encoding="utf-8",
    )
    from src.utils.config import tags_dir_path

    assert tags_dir_path(cfg_dir) == icloud.resolve()


def test_bookmarks_file_path_from_config(tmp_path: Path) -> None:
    target = tmp_path / "my-bookmarks.html"
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text(
        f"chrome:\n  bookmarks_file: {target}\n",
        encoding="utf-8",
    )
    from src.utils.config import bookmarks_file_path

    assert bookmarks_file_path(cfg_dir) == target.resolve()


def test_bookmarks_file_path_env_override(tmp_path: Path, monkeypatch) -> None:
    override = tmp_path / "env-bookmarks.html"
    monkeypatch.setenv("CLI_BOOKMARKS_FILE", str(override))
    from src.utils.config import bookmarks_file_path

    assert bookmarks_file_path() == override.resolve()


def test_notion_pairs_file_split_from_task_root(tmp_path: Path) -> None:
    private_root = tmp_path / "private" / "tasks"
    private_root.mkdir(parents=True)
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text(
        f"notion:\n  task_root: {private_root}\n  pairs_file: config/notion/tasks.pairs.json\n",
        encoding="utf-8",
    )
    manifest = project_root() / "config" / "notion" / "tasks.pairs.json"
    from src.utils.config import notion_pairs_file, notion_task_root

    assert notion_task_root(cfg_dir) == private_root.resolve()
    assert notion_pairs_file(cfg_dir) == manifest.resolve()


def test_notion_pairs_file_bare_name_under_task_root(tmp_path: Path) -> None:
    task_root = tmp_path / "tasks"
    task_root.mkdir()
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text(
        f"notion:\n  task_root: {task_root}\n  pairs_file: tasks.pairs.json\n",
        encoding="utf-8",
    )
    from src.utils.config import notion_pairs_file

    assert notion_pairs_file(cfg_dir) == (task_root / "tasks.pairs.json").resolve()


def test_notion_body_template_file() -> None:
    from src.utils.config import notion_body_template_file

    path = notion_body_template_file()
    assert path.name == "body.md"
    assert path.is_file()
    assert "Steps" in path.read_text(encoding="utf-8")


def test_tags_dir_path_expands_tilde(tmp_path: Path, monkeypatch) -> None:
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    target = tmp_path / "git-tags"
    (cfg_dir / "config.yaml").write_text(
        f"backup:\n  tags_dir: {target}\n",
        encoding="utf-8",
    )
    from src.utils.config import tags_dir_path

    assert tags_dir_path(cfg_dir) == target.resolve()


def test_default_config_dir_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLI_CONFIG_DIR", str(tmp_path))
    assert default_config_dir() == tmp_path


def test_load_yaml_missing_returns_empty(tmp_path: Path) -> None:
    assert load_yaml(tmp_path / "missing.yaml") == {}


def test_load_yaml_invalid_mapping_raises(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("- not-a-map\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        load_yaml(path)


def test_load_config_merges_files(tmp_path: Path) -> None:
    (tmp_path / "config.yaml").write_text(
        "chrome:\n  profile: Work\nbackup:\n  repositories:\n    - path: /path/a\n",
        encoding="utf-8",
    )
    (tmp_path / "drives.yaml").write_text("drives:\n  google: true\n", encoding="utf-8")
    cfg = load_config(tmp_path)
    assert cfg.chrome.profile == "Work"
    assert len(cfg.backup.repositories) == 1
    assert cfg.backup.repositories[0].path == "/path/a"
    assert cfg.drives.google.enabled is True


def test_utils_yaml_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "cfg.yaml"
    dump_yaml(path, {"a": 1})
    assert utils_load_yaml(path) == {"a": 1}
    assert utils_load_yaml(tmp_path / "none.yaml") == {}


def test_utils_yaml_invalid_raises(tmp_path: Path) -> None:
    path = tmp_path / "list.yaml"
    path.write_text("[1, 2]\n", encoding="utf-8")
    with pytest.raises(ValueError):
        utils_load_yaml(path)


def test_fs_helpers(tmp_path: Path) -> None:
    dest = tmp_path / "out" / "file.txt"
    src = tmp_path / "src.txt"
    src.write_text("data", encoding="utf-8")
    fs.atomic_replace(src, dest)
    assert dest.read_text(encoding="utf-8") == "data"
    assert fs.ensure_dir(tmp_path / "a" / "b") == tmp_path / "a" / "b"


def test_sha256_file(tmp_path: Path) -> None:
    path = tmp_path / "f.bin"
    path.write_bytes(b"hello")
    digest = hashing.sha256_file(path)
    assert len(digest) == 64


def test_zip_create_and_extract(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "a.txt").write_text("one", encoding="utf-8")
    archive = tmp_path / "out.zip"
    zip_util.create_zip(source, archive)
    extract = tmp_path / "extracted"
    zip_util.extract_zip(archive, extract)
    assert (extract / "a.txt").read_text(encoding="utf-8") == "one"


def test_retry_succeeds_after_failure() -> None:
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 2:
            raise NotionError("down", status_code=503)
        return "ok"

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.utils.external_client.time.sleep", lambda _: None)
        assert retry.retry(flaky, attempts=3, delay=0) == "ok"


def test_retry_raises_external_call_error() -> None:
    def always_fail() -> None:
        raise RuntimeError("fail")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.utils.external_client.time.sleep", lambda _: None)
        with pytest.raises(ExternalCallError, match="fail"):
            retry.retry(always_fail, attempts=2, delay=0)


def test_run_git_raises_on_failure(tmp_path: Path) -> None:
    with pytest.raises(GitCommandError):
        run_git(["status"], cwd=str(tmp_path), check=True)


def test_git_command_error_message() -> None:
    err = GitCommandError(["git", "x"], 1, "boom")
    assert "boom" in str(err)
    assert err.returncode == 1


def test_tag_zip_basename_and_parse() -> None:
    from src.utils.config import default_zip_path, tag_from_zip_stem, tag_zip_basename

    assert tag_zip_basename("private", "2026-06-23") == "private-2026-06-23"
    assert tag_from_zip_stem("private", "private-2026-06-23") == "2026-06-23"
    assert tag_from_zip_stem("private", "2026-06-23") == "2026-06-23"  # legacy
    assert default_zip_path("private", "2026-06-23").name == "private-2026-06-23.zip"


def test_require_confirmation_with_yes() -> None:
    require_confirmation("go?", yes=True)
