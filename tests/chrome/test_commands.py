"""CLI tests for cli chrome bookmarks ingest/deploy."""

from __future__ import annotations

import json
import time
import zipfile
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from src.services.bookmark_sync import newest_html_export, wait_for_exported_html
from src.cli import app

runner = CliRunner()


@patch("src.commands.chrome.bookmarks_file_path")
@patch("src.commands.chrome.chrome_downloads_dir")
def test_chrome_bookmarks_merge(
    mock_downloads: object,
    mock_path: object,
    tmp_path: Path,
) -> None:
    backup = tmp_path / "backup.html"
    backup.write_text(
        '<dl><p><dt><a href="https://a.example">A</a></dt></dl><p>',
        encoding="utf-8",
    )
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    (downloads / "export.html").write_text(
        '<dl><p><dt><a href="https://b.example">B</a></dt></dl><p>',
        encoding="utf-8",
    )
    mock_path.return_value = backup
    mock_downloads.return_value = downloads
    result = runner.invoke(
        app,
        ["chrome", "bookmarks", "merge"],
        env={"CLI_SKIP_CHROME_AUTOMATION": "1"},
    )
    assert result.exit_code == 0
    assert "https://b.example" in backup.read_text(encoding="utf-8")


@patch("src.commands.chrome.bookmarks_file_path")
@patch("src.commands.chrome.chrome_snapshots_dir")
def test_chrome_bookmarks_snapshot(
    mock_snapshots: object,
    mock_path: object,
    tmp_path: Path,
) -> None:
    backup = tmp_path / "backup.html"
    backup.write_text("<html></html>", encoding="utf-8")
    snapshots = tmp_path / "snapshots"
    mock_path.return_value = backup
    mock_snapshots.return_value = snapshots
    result = runner.invoke(app, ["chrome", "bookmarks", "snapshot"])
    assert result.exit_code == 0
    assert "snapshot" in result.stdout
    assert list(snapshots.glob("Default-*.html"))


def test_chrome_photos_list_empty(tmp_path: Path) -> None:
    photos = tmp_path / "photos"
    photos.mkdir()
    with (
        patch("src.commands.chrome.photos_dir_path", return_value=photos),
    ):
        result = runner.invoke(app, ["chrome", "photos", "list", "--format", "json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["albums"] == []


@patch("src.commands.chrome.photos_dir_path")
@patch("src.commands.chrome.photos_takeout_dir")
def test_chrome_photos_ingest(mock_takeout: object, mock_photos: object, tmp_path: Path) -> None:
    photos = tmp_path / "photos"
    takeout_dir = tmp_path / "Downloads"
    takeout_dir.mkdir()
    zip_path = takeout_dir / "takeout.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("Takeout/Google Photos/Trip/photo.jpg", b"jpeg")
    mock_photos.return_value = photos
    mock_takeout.return_value = takeout_dir
    result = runner.invoke(
        app,
        ["chrome", "photos", "ingest", "--dry-run", "--format", "json"],
        env={"CLI_SKIP_CHROME_AUTOMATION": "1"},
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["media_files"] == 1
    assert payload["albums"] == ["trip"]


def test_chrome_photos_list_missing_dir() -> None:
    with patch(
        "src.commands.chrome.photos_dir_path",
        side_effect=FileNotFoundError("chrome.photos_dir is not configured"),
    ):
        result = runner.invoke(app, ["chrome", "photos", "list"])
    assert result.exit_code == 1
    assert "photos_dir" in result.output


@patch("src.commands.chrome.bookmarks_file_path")
@patch("src.commands.chrome.chrome_downloads_dir")
def test_chrome_bookmarks_ingest(mock_downloads, mock_path, tmp_path: Path) -> None:
    dest = tmp_path / "bookmarks.html"
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    exported = downloads / "export.html"
    exported.write_text("<html>bookmarks</html>", encoding="utf-8")
    mock_path.return_value = dest
    mock_downloads.return_value = downloads
    result = runner.invoke(
        app,
        ["chrome", "bookmarks", "ingest"],
        env={"CLI_SKIP_CHROME_AUTOMATION": "1"},
    )
    assert result.exit_code == 0
    assert "ingested" in result.stdout
    assert dest.read_text(encoding="utf-8") == "<html>bookmarks</html>"


@patch("src.commands.chrome.bookmarks_file_path")
def test_chrome_bookmarks_deploy(mock_path, tmp_path: Path) -> None:
    src = tmp_path / "bookmarks.html"
    src.write_text("<html></html>", encoding="utf-8")
    mock_path.return_value = src
    result = runner.invoke(app, ["chrome", "bookmarks", "deploy"])
    assert result.exit_code == 0
    assert "ready" in result.stdout


@patch("src.commands.chrome.bookmarks_file_path")
def test_chrome_bookmarks_deploy_missing_backup(mock_path, tmp_path: Path) -> None:
    mock_path.return_value = tmp_path / "missing.html"
    result = runner.invoke(app, ["chrome", "bookmarks", "deploy"])
    assert result.exit_code != 0
    assert "Backup not found" in result.output


def test_legacy_bookmarks_export_alias_calls_ingest(tmp_path: Path) -> None:
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    (downloads / "export.html").write_text("<html></html>", encoding="utf-8")
    with (
        patch("src.commands.chrome.bookmarks_file_path", return_value=tmp_path / "b.html"),
        patch("src.commands.chrome.chrome_downloads_dir", return_value=downloads),
    ):
        result = runner.invoke(app, ["bookmarks", "export"], env={"CLI_SKIP_CHROME_AUTOMATION": "1"})
    assert result.exit_code == 0
    assert "ingested" in result.stdout


@patch("src.commands.chrome.bookmarks_file_path")
@patch("src.commands.chrome.chrome_downloads_dir")
def test_chrome_legacy_export_alias_calls_ingest(mock_downloads, mock_path, tmp_path: Path) -> None:
    dest = tmp_path / "bookmarks.html"
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    (downloads / "export.html").write_text("<html></html>", encoding="utf-8")
    mock_path.return_value = dest
    mock_downloads.return_value = downloads
    result = runner.invoke(app, ["chrome", "bookmarks", "export"], env={"CLI_SKIP_CHROME_AUTOMATION": "1"})
    assert result.exit_code == 0
    assert "ingested" in result.stdout


@patch("src.commands.chrome.bookmarks_file_path")
def test_chrome_legacy_import_alias_calls_deploy(mock_path, tmp_path: Path) -> None:
    src = tmp_path / "bookmarks.html"
    src.write_text("<html></html>", encoding="utf-8")
    mock_path.return_value = src
    result = runner.invoke(app, ["chrome", "bookmarks", "import"])
    assert result.exit_code == 0
    assert "ready" in result.stdout


def test_wait_download_selects_newest_html(tmp_path: Path) -> None:
    older = tmp_path / "older.html"
    newer = tmp_path / "newer.html"
    older.write_text("<html>old</html>")
    time.sleep(1.1)
    newer.write_text("<html>new</html>")

    assert newest_html_export(tmp_path) == newer


def test_wait_download_times_out_without_html(tmp_path: Path) -> None:
    partial = tmp_path / "bookmarks.html.crdownload"
    partial.write_text("partial")
    assert newest_html_export(tmp_path) is None
    try:
        wait_for_exported_html(tmp_path, timeout=0, interval=0)
    except TimeoutError:
        pass
    else:
        raise AssertionError("expected TimeoutError")
