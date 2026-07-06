"""Terminal-first bookmark sync helpers."""

from __future__ import annotations

import os
import re
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html import escape as html_escape
from pathlib import Path

from src.models.bookmark import BookmarkEntry

_ANCHOR_RE = re.compile(
    r"<dt>\s*<a\b[^>]*\bhref=(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+))[^>]*>(.*?)</a>\s*</dt>",
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class MergeResult:
    added: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    dry_run: bool = False


def export_bookmarks(
    dest: Path,
    *,
    downloads_dir: Path,
    source: Path | None = None,
    timeout: int = 120,
    interval: float = 1.0,
    since_epoch: float | None = None,
) -> Path:
    """Copy an exported Chrome bookmarks HTML file into the configured backup path."""

    dest = dest.expanduser().resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    src = source.expanduser().resolve() if source else wait_for_exported_html(
        downloads_dir.expanduser().resolve(),
        timeout=timeout,
        interval=interval,
        since_epoch=since_epoch,
    )
    if not src.is_file():
        raise FileNotFoundError(f"bookmarks source not found: {src}")
    tmp = dest.with_name(f"{dest.name}.tmp.{os.getpid()}")
    shutil.copyfile(src, tmp)
    tmp.replace(dest)
    if source is None and src.parent == downloads_dir.expanduser().resolve():
        src.unlink(missing_ok=True)
    return dest


def import_bookmarks(src: Path) -> Path:
    """Validate that the configured bookmarks backup is ready for browser import."""

    src = src.expanduser().resolve()
    if not src.is_file():
        raise FileNotFoundError(f"Backup not found: {src}")
    if src.stat().st_size == 0:
        raise ValueError(f"Backup file is empty: {src}")
    return src


def parse_bookmark_entries(html: str) -> list[BookmarkEntry]:
    """Extract bookmark links from Netscape-style HTML export."""

    entries: list[BookmarkEntry] = []
    for match in _ANCHOR_RE.finditer(html):
        url = (match.group(1) or match.group(2) or match.group(3) or "").strip()
        title = re.sub(r"<[^>]+>", "", match.group(4) or "").strip()
        if url:
            entries.append(BookmarkEntry(title=title or url, url=url))
    return entries


def _normalize_url(url: str) -> str:
    return url.strip().casefold()


def _append_entries(html: str, entries: list[BookmarkEntry]) -> str:
    if not entries:
        return html
    block = "".join(
        f'    <dt><a href="{html_escape(entry.url)}">{html_escape(entry.title)}</a></dt>\n'
        for entry in entries
    )
    lower = html.lower()
    idx = lower.rfind("</dl>")
    if idx == -1:
        return html + f"\n<dl><p>\n{block}</dl><p>\n"
    return html[:idx] + block + html[idx:]


def merge_bookmarks(
    backup: Path,
    source: Path,
    *,
    dry_run: bool = False,
) -> MergeResult:
    """Merge new bookmark URLs from source HTML into backup (dedupe by URL)."""

    source = source.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"bookmarks source not found: {source}")
    source_html = source.read_text(encoding="utf-8", errors="replace")
    source_entries = parse_bookmark_entries(source_html)
    result = MergeResult(dry_run=dry_run)

    backup = backup.expanduser().resolve()
    if backup.is_file():
        existing = {_normalize_url(entry.url) for entry in parse_bookmark_entries(backup.read_text(encoding="utf-8", errors="replace"))}
    else:
        existing = set()

    to_add: list[BookmarkEntry] = []
    for entry in source_entries:
        key = _normalize_url(entry.url)
        if key in existing:
            result.skipped.append(entry.url)
            continue
        to_add.append(entry)
        result.added.append(entry.url)
        existing.add(key)

    if dry_run or not to_add:
        return result

    backup.parent.mkdir(parents=True, exist_ok=True)
    base_html = backup.read_text(encoding="utf-8", errors="replace") if backup.is_file() else (
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>\n"
        "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\">\n"
        "<title>Bookmarks</title>\n<h1>Bookmarks</h1>\n<dl><p>\n</dl><p>\n"
    )
    merged = _append_entries(base_html, to_add)
    tmp = backup.with_name(f"{backup.name}.tmp.{os.getpid()}")
    tmp.write_text(merged, encoding="utf-8")
    tmp.replace(backup)
    return result


def snapshot_bookmarks(
    backup: Path,
    snapshots_dir: Path,
    profile: str,
    *,
    retention: int = 0,
) -> Path:
    """Copy backup HTML to a timestamped snapshot file."""

    backup = backup.expanduser().resolve()
    import_bookmarks(backup)
    snapshots_dir = snapshots_dir.expanduser().resolve()
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    safe_profile = re.sub(r"[^\w.-]+", "-", profile.strip() or "Default")
    dest = snapshots_dir / f"{safe_profile}-{stamp}.html"
    shutil.copy2(backup, dest)
    if retention > 0:
        pattern = f"{safe_profile}-*.html"
        existing = sorted(snapshots_dir.glob(pattern), key=lambda p: p.stat().st_mtime)
        for old in existing[:-retention]:
            old.unlink(missing_ok=True)
    return dest


def wait_for_exported_html(
    downloads_dir: Path,
    *,
    timeout: int = 120,
    interval: float = 1.0,
    since_epoch: float | None = None,
) -> Path:
    """Poll a downloads directory for the newest completed HTML export."""

    if not downloads_dir.is_dir():
        raise FileNotFoundError(f"Downloads directory not found: {downloads_dir}")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        newest = newest_html_export(downloads_dir, since_epoch=since_epoch)
        if newest:
            return newest
        time.sleep(interval)
    raise TimeoutError(f"Timed out after {timeout}s waiting for HTML download in {downloads_dir}")


def newest_html_export(downloads_dir: Path, *, since_epoch: float | None = None) -> Path | None:
    newest: Path | None = None
    newest_mtime = 0.0
    for path in downloads_dir.glob("*.html"):
        if path.name.endswith(".crdownload") or not path.is_file():
            continue
        mtime = path.stat().st_mtime
        if since_epoch is not None and mtime <= since_epoch:
            continue
        if mtime > newest_mtime:
            newest = path
            newest_mtime = mtime
    return newest
