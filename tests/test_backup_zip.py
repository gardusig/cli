"""Encrypted and plain tag zip creation."""

from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

import pytest

from gardusig_cli.services.backup_zip import archive_tag_zip


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "t@t.com"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "T"], check=True)
    (path / "README.md").write_text("secret\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "commit", "-m", "init"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "tag", "-a", "v1", "-m", "v1"], check=True)


def test_archive_tag_zip_plain(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    out = tmp_path / "plain.zip"
    archive_tag_zip(repo, "v1", out, encrypted=False)
    assert out.is_file()
    with zipfile.ZipFile(out) as zf:
        assert "README.md" in zf.namelist()


def test_archive_tag_zip_encrypted(tmp_path: Path) -> None:
    if subprocess.run(["which", "zip"], capture_output=True).returncode != 0:
        pytest.fail("zip is required for encrypted tag archives (install via apt/brew)")
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    out = tmp_path / "secret.zip"
    archive_tag_zip(repo, "v1", out, encrypted=True, password="test-pass")
    assert out.is_file()


def test_archive_tag_zip_encrypted_requires_password(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    with pytest.raises(RuntimeError, match="BACKUP_ZIP_PASSWORD"):
        archive_tag_zip(repo, "v1", tmp_path / "x.zip", encrypted=True, password=None)
