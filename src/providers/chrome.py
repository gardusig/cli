"""Chrome provider adapter (legacy; bookmark ops live in bookmark_sync)."""

from __future__ import annotations

from pathlib import Path

from src.services import bookmark_sync

name = "chrome"


def export_bookmarks(profile: str, dest: str) -> None:
    """Legacy provider entry — use bookmark_sync.export_bookmarks instead."""

    bookmark_sync.export_bookmarks(
        Path(dest),
        downloads_dir=Path.home() / "Downloads",
        source=None,
    )


def import_bookmarks(profile: str, src: str) -> None:
    """Legacy provider entry — use bookmark_sync.import_bookmarks instead."""

    bookmark_sync.import_bookmarks(Path(src))
