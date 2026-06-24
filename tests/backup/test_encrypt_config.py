"""Backup encryption config helpers."""

from __future__ import annotations

from tests.constants import ROOT

from pathlib import Path

from gardusig_cli.utils.config import backup_repository_entry, repo_encrypt_backup


def test_repo_encrypt_backup_flag(tmp_path: Path) -> None:
    repo = tmp_path / "private"
    repo.mkdir()
    public = tmp_path / "public"
    public.mkdir()
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text(
        "backup:\n"
        "  repositories:\n"
        f"    - path: {public}\n"
        f"    - path: {repo}\n"
        "      encrypted: true\n",
        encoding="utf-8",
    )
    assert repo_encrypt_backup(public, cfg_dir) is False
    assert repo_encrypt_backup(repo, cfg_dir) is True
    assert backup_repository_entry(repo, cfg_dir) is not None
    assert backup_repository_entry(repo, cfg_dir).encrypted is True
