"""Coverage for placeholders, review runner, __main__, and gated git writes."""

from __future__ import annotations

from tests.constants import ROOT

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.internal.write.git import gated_git_write, read_git_snapshot
from src.providers import google_drive, icloud_drive, notion, onedrive, proton_drive
from src.services import drive_sync, notion_sync
from src.services.notion_sync import cleanup_board
from src.services.git_review import run_review
from src.utils.http import default_http_timeout

STUB_CALLS: list[tuple[Callable[..., Any], tuple[Any, ...]]] = [
    (google_drive.delete, ("/b",)),
    (icloud_drive.upload, ("/a", "/b")),
    (icloud_drive.download, ("/b", "/a")),
    (icloud_drive.list_files, ("",)),
    (icloud_drive.delete, ("/b",)),
    (notion.export_tasks, ("db", "/dest")),
    (notion.import_tasks, ("db", "/src")),
    (onedrive.delete, ("/b",)),
    (proton_drive.delete, ("/b",)),
    (drive_sync.upload_backup, ("/local", "google")),
    (drive_sync.download_latest, ("google", "/dest")),
]


_REAL_HTTPX_CLIENT = httpx.Client


def test_notion_sync_with_mocks(monkeypatch, tmp_path: Path) -> None:
    from src.utils.config import NotionConfig

    cfg = NotionConfig(database_id="db")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path.endswith("/query"):
            return httpx.Response(200, json={"results": [], "has_more": False})
        return httpx.Response(200, json={"id": "ok"})

    def _client_factory(**kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        kwargs.setdefault("base_url", "https://api.notion.com/v1")
        kwargs.setdefault("timeout", default_http_timeout())
        return _REAL_HTTPX_CLIENT(**kwargs)

    with patch(
        "src.providers.notion.httpx.Client",
        side_effect=_client_factory,
    ):
        assert cleanup_board(token="t", config=cfg).processed == 0


@pytest.mark.parametrize("fn,args", STUB_CALLS)
def test_placeholder_raises_not_implemented(fn: Callable[..., Any], args: tuple[Any, ...]) -> None:
    with pytest.raises(NotImplementedError):
        fn(*args)


def test_main_module_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "src", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "git" in result.stdout


@patch("src.services.git_review.subprocess.run")
def test_run_review_quick_skips_pytest(mock_run: MagicMock, tmp_path) -> None:
    root = tmp_path
    mock_run.return_value = MagicMock(returncode=0)
    with patch("src.services.git_review.project_root", return_value=root):
        assert run_review(install=False, quick=True) == 0
    calls = [c.args[0] for c in mock_run.call_args_list if c.args]
    assert calls == [["cli", "test", "python", "command-surface", str(root)]]


@patch("src.services.git_review.subprocess.run")
def test_run_review_runs_docker_unit_tests(mock_run: MagicMock, tmp_path) -> None:
    root = tmp_path
    mock_run.return_value = MagicMock(returncode=0)
    with patch("src.services.git_review.project_root", return_value=root):
        assert run_review(install=False, quick=False) == 0
    command_surface = [
        c
        for c in mock_run.call_args_list
        if c.args and c.args[0] == ["cli", "test", "python", "command-surface", str(root)]
    ]
    unit_gate = [
        c
        for c in mock_run.call_args_list
        if c.args and c.args[0] == ["cli", "test", "python", "unit", str(root)]
    ]
    assert command_surface, "expected cli test python command-surface"
    assert unit_gate, "expected cli test python unit"


def test_gated_git_write_with_yes() -> None:
    svc = MagicMock()
    with patch("src.internal.write.git.git_worktree_snapshot") as mock_snap:
        mock_snap.return_value.summary_lines.return_value = ["branch: main"]
        result = gated_git_write(svc, "push", lambda: 42, yes=True)
    assert result == 42


def test_read_git_snapshot() -> None:
    svc = MagicMock()
    with patch("src.internal.write.git.git_worktree_snapshot") as mock_snap:
        snap = read_git_snapshot(svc)
    assert snap is mock_snap.return_value
