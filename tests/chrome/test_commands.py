"""CLI tests for cli chrome bookmarks ingest/deploy."""

from __future__ import annotations

from tests.constants import ROOT

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()


@patch("src.commands.chrome.subprocess.run")
@patch("src.commands.chrome.bookmarks_file_path")
def test_chrome_bookmarks_ingest(mock_path: MagicMock, mock_run: MagicMock, tmp_path: Path) -> None:
    dest = tmp_path / "bookmarks.html"
    mock_path.return_value = dest
    mock_run.return_value = MagicMock(returncode=0)
    result = runner.invoke(app, ["chrome", "bookmarks", "ingest"])
    assert result.exit_code == 0
    assert "ingested" in result.stdout
    mock_run.assert_called_once()


@patch("src.commands.chrome.subprocess.run")
@patch("src.commands.chrome.bookmarks_file_path")
def test_chrome_bookmarks_deploy(mock_path: MagicMock, mock_run: MagicMock, tmp_path: Path) -> None:
    src = tmp_path / "bookmarks.html"
    src.write_text("<html></html>", encoding="utf-8")
    mock_path.return_value = src
    mock_run.return_value = MagicMock(returncode=0)
    result = runner.invoke(app, ["chrome", "bookmarks", "deploy"])
    assert result.exit_code == 0
    assert "deployed" in result.stdout


@patch("src.commands.chrome.bookmarks_file_path")
def test_chrome_bookmarks_deploy_missing_backup(mock_path: MagicMock, tmp_path: Path) -> None:
    mock_path.return_value = tmp_path / "missing.html"
    result = runner.invoke(app, ["chrome", "bookmarks", "deploy"])
    assert result.exit_code != 0
    assert "Backup not found" in result.stdout


def test_legacy_bookmarks_export_alias_calls_ingest() -> None:
    with patch("src.commands.chrome.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        with patch("src.commands.chrome.bookmarks_file_path", return_value=Path("/tmp/b.html")):
            result = runner.invoke(app, ["bookmarks", "export"])
    assert result.exit_code == 0
    assert "ingested" in result.stdout


@patch("src.commands.chrome.subprocess.run")
@patch("src.commands.chrome.bookmarks_file_path")
def test_chrome_legacy_export_alias_calls_ingest(mock_path: MagicMock, mock_run: MagicMock, tmp_path: Path) -> None:
    dest = tmp_path / "bookmarks.html"
    mock_path.return_value = dest
    mock_run.return_value = MagicMock(returncode=0)
    result = runner.invoke(app, ["chrome", "bookmarks", "export"])
    assert result.exit_code == 0
    assert "ingested" in result.stdout


@patch("src.commands.chrome.subprocess.run")
@patch("src.commands.chrome.bookmarks_file_path")
def test_chrome_legacy_import_alias_calls_deploy(mock_path: MagicMock, mock_run: MagicMock, tmp_path: Path) -> None:
    src = tmp_path / "bookmarks.html"
    src.write_text("<html></html>", encoding="utf-8")
    mock_path.return_value = src
    mock_run.return_value = MagicMock(returncode=0)
    result = runner.invoke(app, ["chrome", "bookmarks", "import"])
    assert result.exit_code == 0
    assert "deployed" in result.stdout


"""Issue #1 bookmark shell script tests (isolated temp dirs)."""


import os
import subprocess
import time
from pathlib import Path

import pytest


FIXTURE = ROOT / "tests" / "fixtures" / "bookmarks.html"
CHROME_DIR = ROOT / "scripts" / "chrome"


def _run_script(name: str, env: dict[str, str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    script = CHROME_DIR / name
    merged = {**os.environ, **env}
    return subprocess.run(
        ["bash", str(script)],
        cwd=ROOT,
        env=merged,
        capture_output=True,
        text=True,
        check=check,
    )


@pytest.fixture
def sandbox(tmp_path: Path) -> dict[str, Path]:
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    data_bookmarks = tmp_path / "data" / "bookmarks"
    data_bookmarks.mkdir(parents=True)
    return {
        "root": tmp_path,
        "downloads": downloads,
        "bookmarks_file": data_bookmarks / "bookmarks.html",
    }


def test_wait_download_selects_newest_html(sandbox: dict[str, Path]) -> None:
    older = sandbox["downloads"] / "older.html"
    newer = sandbox["downloads"] / "newer.html"
    older.write_text("<html>old</html>")
    time.sleep(1.1)
    newer.write_text("<html>new</html>")

    result = _run_script(
        "wait-download.sh",
        {
            "CLI_DOWNLOADS_DIR": str(sandbox["downloads"]),
            "CLI_DOWNLOAD_TIMEOUT": "5",
        },
    )
    assert result.returncode == 0
    assert result.stdout.strip().endswith("newer.html")


def test_wait_download_ignores_crdownload(sandbox: dict[str, Path]) -> None:
    partial = sandbox["downloads"] / "bookmarks.html.crdownload"
    partial.write_text("partial")
    result = _run_script(
        "wait-download.sh",
        {
            "CLI_DOWNLOADS_DIR": str(sandbox["downloads"]),
            "CLI_DOWNLOAD_TIMEOUT": "2",
        },
        check=False,
    )
    assert result.returncode != 0


def test_export_from_fixture(sandbox: dict[str, Path]) -> None:
    result = _run_script(
        "export.sh",
        {
            "CLI_ROOT": str(sandbox["root"]),
            "CLI_BOOKMARKS_FILE": str(sandbox["bookmarks_file"]),
            "CLI_SKIP_CHROME_AUTOMATION": "1",
            "CLI_BOOKMARKS_FIXTURE": str(FIXTURE),
        },
    )
    assert result.returncode == 0
    assert sandbox["bookmarks_file"].exists()
    assert "Cli Test Bookmark" in sandbox["bookmarks_file"].read_text()


def test_export_overwrites_previous_backup(sandbox: dict[str, Path]) -> None:
    sandbox["bookmarks_file"].write_text("<html>stale</html>")
    _run_script(
        "export.sh",
        {
            "CLI_ROOT": str(sandbox["root"]),
            "CLI_BOOKMARKS_FILE": str(sandbox["bookmarks_file"]),
            "CLI_SKIP_CHROME_AUTOMATION": "1",
            "CLI_BOOKMARKS_FIXTURE": str(FIXTURE),
        },
    )
    content = sandbox["bookmarks_file"].read_text()
    assert "stale" not in content
    assert "Cli Test Bookmark" in content


def test_export_from_downloads_dir(sandbox: dict[str, Path]) -> None:
    downloaded = sandbox["downloads"] / "bookmarks_export.html"
    downloaded.write_text(FIXTURE.read_text())
    result = _run_script(
        "export.sh",
        {
            "CLI_ROOT": str(sandbox["root"]),
            "CLI_DOWNLOADS_DIR": str(sandbox["downloads"]),
            "CLI_BOOKMARKS_FILE": str(sandbox["bookmarks_file"]),
            "CLI_SKIP_CHROME_AUTOMATION": "1",
        },
    )
    assert result.returncode == 0
    assert sandbox["bookmarks_file"].exists()
    assert "Cli Test Bookmark" in sandbox["bookmarks_file"].read_text()
    assert not downloaded.exists()


def test_import_succeeds_with_backup(sandbox: dict[str, Path]) -> None:
    sandbox["bookmarks_file"].write_text(FIXTURE.read_text())
    result = _run_script(
        "import.sh",
        {
            "CLI_ROOT": str(sandbox["root"]),
            "CLI_BOOKMARKS_FILE": str(sandbox["bookmarks_file"]),
            "CLI_SKIP_CHROME_AUTOMATION": "1",
        },
    )
    assert result.returncode == 0
    assert "Import complete" in result.stdout


def test_import_fails_without_backup(sandbox: dict[str, Path]) -> None:
    result = _run_script(
        "import.sh",
        {
            "CLI_ROOT": str(sandbox["root"]),
            "CLI_BOOKMARKS_FILE": str(sandbox["bookmarks_file"]),
            "CLI_SKIP_CHROME_AUTOMATION": "1",
        },
        check=False,
    )
    assert result.returncode != 0
    assert "Backup not found" in result.stderr + result.stdout
