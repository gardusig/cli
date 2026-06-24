"""Unit tests for drive_sync internal helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from gardusig_cli.services.drive_sync import _scan_local_files, upload_missing
from gardusig_cli.utils.external_client import ExternalCallError
from tests.drive_harness import InMemoryDriveProvider


def test_scan_local_files_empty_when_missing(tmp_path: Path) -> None:
    assert _scan_local_files(tmp_path / "missing") == []


def test_scan_local_files_returns_posix_relative_paths(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "one.txt").write_text("1", encoding="utf-8")
    (tmp_path / "b.txt").write_text("2", encoding="utf-8")
    assert _scan_local_files(tmp_path) == ["a/one.txt", "b.txt"]


def test_upload_missing_raises_on_list_error(tmp_path: Path) -> None:
    class BrokenProvider(InMemoryDriveProvider):
        def list_files(self, prefix: str) -> list[str]:
            raise RuntimeError("cloud down")

    with pytest.raises(ExternalCallError) as exc_info:
        upload_missing(tmp_path, BrokenProvider(), "remote")

    assert "cloud down" in exc_info.value.user_message
