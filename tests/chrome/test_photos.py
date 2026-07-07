"""Unit tests for Google Photos Takeout ingest."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from src.services.photos_sync import ingest_takeout, list_albums, photos_status


def _write_takeout_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("Takeout/Google Photos/Summer/one.jpg", b"jpeg")
        archive.writestr("Takeout/Google Photos/Summer/two.png", b"png")


def test_ingest_takeout_creates_albums_and_manifest(tmp_path: Path) -> None:
    photos_dir = tmp_path / "photos"
    takeout_dir = tmp_path / "Downloads"
    takeout_dir.mkdir()
    zip_path = takeout_dir / "takeout.zip"
    _write_takeout_zip(zip_path)

    result = ingest_takeout(photos_dir, takeout_dir, source=zip_path)
    assert result.media_files == 2
    assert result.albums == ["summer"]
    albums = list_albums(photos_dir)
    assert len(albums) == 1
    assert albums[0].media_count == 2
    manifest = json.loads((photos_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["albums"][0]["slug"] == "summer"


def test_ingest_takeout_dry_run_does_not_write(tmp_path: Path) -> None:
    photos_dir = tmp_path / "photos"
    takeout_dir = tmp_path / "Downloads"
    takeout_dir.mkdir()
    zip_path = takeout_dir / "takeout.zip"
    _write_takeout_zip(zip_path)

    result = ingest_takeout(photos_dir, takeout_dir, source=zip_path, dry_run=True)
    assert result.media_files == 2
    assert not (photos_dir / "albums").exists()


def test_photos_status_reports_inventory(tmp_path: Path) -> None:
    photos_dir = tmp_path / "photos"
    takeout_dir = tmp_path / "Downloads"
    takeout_dir.mkdir()
    zip_path = takeout_dir / "takeout.zip"
    _write_takeout_zip(zip_path)
    ingest_takeout(photos_dir, takeout_dir, source=zip_path)

    status = photos_status(photos_dir)
    assert status["album_count"] == 1
    assert status["media_count"] == 2


def test_ingest_takeout_missing_google_photos_dir(tmp_path: Path) -> None:
    photos_dir = tmp_path / "photos"
    bad_zip = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad_zip, "w") as archive:
        archive.writestr("Takeout/Other/data.txt", "x")
    with pytest.raises(FileNotFoundError, match="Google Photos"):
        ingest_takeout(photos_dir, tmp_path, source=bad_zip)
