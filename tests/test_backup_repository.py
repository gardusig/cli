"""Backup repository service tests."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest

from cli.services.backup_repository import (
    RepoBackupStatus,
    format_status_lines,
    ingest_repositories,
    sync_repo,
)


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "t@t.com"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "T"], check=True)
    (path / "README.md").write_text("hi\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "commit", "-m", "init"], check=True, capture_output=True)


def test_sync_repo_idempotent(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "demo-repo"
    repo.mkdir()
    _init_repo(repo)
    subprocess.run(["git", "-C", str(repo), "tag", "-a", "v1", "-m", "v1"], check=True)
    tags_root = tmp_path / "tag-folder"
    tags_root.mkdir()
    monkeypatch.setattr("cli.services.backup_repository.tags_dir_path", lambda _=None: tags_root)

    first = sync_repo(str(repo))
    assert first.created == ["v1"]
    second = sync_repo(str(repo))
    assert second.replaced == ["v1"]
    assert (tags_root / "demo-repo" / "v1.zip").is_file()


def test_ingest_repositories_all_configured(monkeypatch, tmp_path: Path) -> None:
    tags_root = tmp_path / "git-tags"
    tags_root.mkdir()
    monkeypatch.setattr("cli.services.backup_repository.tags_dir_path", lambda _=None: tags_root)
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "repo-b"
    for repo in (repo_a, repo_b):
        repo.mkdir()
        _init_repo(repo)
        subprocess.run(["git", "-C", str(repo), "tag", "-a", "v1", "-m", "v1"], check=True)
    (cfg_dir / "config.yaml").write_text(
        "backup:\n  repositories:\n"
        f"    - path: {repo_a}\n"
        f"    - path: {repo_b}\n",
        encoding="utf-8",
    )
    rows = ingest_repositories(config_dir=cfg_dir)
    assert len(rows) == 2
    assert all(result.created == ["v1"] for _, result in rows)


def test_ingest_repositories_single_path(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "multi"
    repo.mkdir()
    _init_repo(repo)
    subprocess.run(["git", "-C", str(repo), "tag", "-a", "t1", "-m", "t1"], check=True)
    tags_root = tmp_path / "git-tags"
    tags_root.mkdir()
    monkeypatch.setattr("cli.services.backup_repository.tags_dir_path", lambda _=None: tags_root)
    rows = ingest_repositories(str(repo))
    assert len(rows) == 1
    assert rows[0][1].created == ["t1"]


def test_format_status_lines() -> None:
    lines = format_status_lines(
        [
            RepoBackupStatus(
                name="demo",
                path=Path("/tmp/demo"),
                git_tags=["a", "b"],
                downloaded=["a"],
                missing=["b"],
            )
        ]
    )
    text = "\n".join(lines)
    assert "demo" in text
    assert "Missing locally" in text
    assert "b" in text


def test_format_status_lines_empty_config() -> None:
    lines = format_status_lines([])
    assert len(lines) == 1
    assert "No repositories configured" in lines[0]


def test_resolve_repo_path_rejects_non_git(tmp_path: Path) -> None:
    from cli.services.backup_repository import resolve_repo_path

    with pytest.raises(RuntimeError, match="Not a git repository"):
        resolve_repo_path(str(tmp_path))


def test_resolve_repo_path_rejects_missing_dir() -> None:
    from cli.services.backup_repository import resolve_repo_path

    with pytest.raises(RuntimeError, match="Not a directory"):
        resolve_repo_path("/no/such/path")


def test_ingest_repositories_no_config_raises(tmp_path: Path) -> None:
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text("backup:\n  repositories: []\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="No repositories configured"):
        ingest_repositories(config_dir=cfg_dir)
