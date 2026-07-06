"""Unit tests for bookmark merge, snapshot, and HTML parsing."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.services.bookmark_sync import merge_bookmarks, parse_bookmark_entries, snapshot_bookmarks

_SAMPLE = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<dl><p>
    <dt><a href="https://existing.example">Existing</a></dt>
</dl><p>
"""

_NEW = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<dl><p>
    <dt><a href="https://existing.example">Dup</a></dt>
    <dt><a href="https://new.example">New</a></dt>
</dl><p>
"""


def test_parse_bookmark_entries_extracts_urls() -> None:
    entries = parse_bookmark_entries(_NEW)
    urls = {entry.url for entry in entries}
    assert urls == {"https://existing.example", "https://new.example"}


def test_merge_bookmarks_adds_new_urls_only(tmp_path: Path) -> None:
    backup = tmp_path / "backup.html"
    source = tmp_path / "source.html"
    backup.write_text(_SAMPLE, encoding="utf-8")
    source.write_text(_NEW, encoding="utf-8")

    result = merge_bookmarks(backup, source)
    assert result.added == ["https://new.example"]
    assert result.skipped == ["https://existing.example"]
    merged = backup.read_text(encoding="utf-8")
    assert "https://new.example" in merged
    assert merged.count("https://existing.example") == 1


def test_merge_bookmarks_dry_run_does_not_write(tmp_path: Path) -> None:
    backup = tmp_path / "backup.html"
    source = tmp_path / "source.html"
    backup.write_text(_SAMPLE, encoding="utf-8")
    source.write_text(_NEW, encoding="utf-8")
    before = backup.read_text(encoding="utf-8")

    result = merge_bookmarks(backup, source, dry_run=True)
    assert result.added == ["https://new.example"]
    assert backup.read_text(encoding="utf-8") == before


def test_merge_bookmarks_creates_backup_when_missing(tmp_path: Path) -> None:
    source = tmp_path / "source.html"
    source.write_text(_NEW, encoding="utf-8")
    backup = tmp_path / "new-backup.html"

    result = merge_bookmarks(backup, source)
    assert len(result.added) == 2
    assert backup.is_file()


def test_merge_bookmarks_missing_source_raises(tmp_path: Path) -> None:
    backup = tmp_path / "backup.html"
    backup.write_text(_SAMPLE, encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        merge_bookmarks(backup, tmp_path / "missing.html")


def test_snapshot_bookmarks_copies_with_retention(tmp_path: Path) -> None:
    backup = tmp_path / "backup.html"
    backup.write_text(_SAMPLE, encoding="utf-8")
    snapshots = tmp_path / "snapshots"

    first = snapshot_bookmarks(backup, snapshots, "Default", retention=1)
    second = snapshot_bookmarks(backup, snapshots, "Default", retention=1)

    assert first.is_file()
    assert second.is_file()
    assert first.name.startswith("Default-")
    remaining = list(snapshots.glob("Default-*.html"))
    assert len(remaining) == 1
    assert remaining[0] == second
