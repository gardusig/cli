"""Google Photos Takeout ingest helpers (file-based, no live API)."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import time
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_NAME = "manifest.json"
ALBUMS_DIR = "albums"
_GOOGLE_PHOTOS_NAMES = ("Google Photos", "Photos")
_MEDIA_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".mp4", ".mov"})


@dataclass
class AlbumRecord:
    slug: str
    title: str
    media_count: int
    path: str


@dataclass
class IngestResult:
    albums: list[str] = field(default_factory=list)
    media_files: int = 0
    source: str = ""
    dry_run: bool = False


def _slugify(name: str) -> str:
    slug = re.sub(r"[^\w.-]+", "-", name.strip()).strip("-").lower()
    return slug or "album"


def manifest_path(photos_dir: Path) -> Path:
    return photos_dir.expanduser().resolve() / MANIFEST_NAME


def _read_manifest_raw(photos_dir: Path) -> dict:
    path = manifest_path(photos_dir)
    if not path.is_file():
        return {"albums": [], "last_ingest": None}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"albums": [], "last_ingest": None}
    if not isinstance(data, dict):
        return {"albums": [], "last_ingest": None}
    albums = data.get("albums")
    if not isinstance(albums, list):
        data["albums"] = []
    return data


def write_manifest(photos_dir: Path, albums: list[AlbumRecord]) -> Path:
    photos_dir = photos_dir.expanduser().resolve()
    photos_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "albums": [
            {
                "slug": album.slug,
                "title": album.title,
                "media_count": album.media_count,
                "path": album.path,
            }
            for album in albums
        ],
        "last_ingest": datetime.now(timezone.utc).isoformat(),
    }
    dest = manifest_path(photos_dir)
    tmp = dest.with_name(f"{dest.name}.tmp.{os.getpid()}")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(dest)
    return dest


def list_albums(photos_dir: Path) -> list[AlbumRecord]:
    photos_dir = photos_dir.expanduser().resolve()
    data = _read_manifest_raw(photos_dir)
    albums: list[AlbumRecord] = []
    for item in data.get("albums", []):
        if not isinstance(item, dict):
            continue
        slug = str(item.get("slug", "")).strip()
        title = str(item.get("title", slug)).strip() or slug
        media_count = int(item.get("media_count", 0) or 0)
        rel = str(item.get("path", "")).strip() or f"{ALBUMS_DIR}/{slug}"
        albums.append(AlbumRecord(slug=slug, title=title, media_count=media_count, path=rel))
    if albums:
        return albums

    root = photos_dir / ALBUMS_DIR
    if not root.is_dir():
        return []
    for album_dir in sorted(root.iterdir()):
        if not album_dir.is_dir():
            continue
        media_count = sum(
            1 for path in album_dir.rglob("*") if path.is_file() and path.suffix.lower() in _MEDIA_SUFFIXES
        )
        slug = album_dir.name
        albums.append(
            AlbumRecord(
                slug=slug,
                title=slug.replace("-", " ").title(),
                media_count=media_count,
                path=f"{ALBUMS_DIR}/{slug}",
            )
        )
    return albums


def photos_status(photos_dir: Path) -> dict[str, object]:
    albums = list_albums(photos_dir)
    media_count = sum(album.media_count for album in albums)
    data = _read_manifest_raw(photos_dir)
    return {
        "photos_dir": str(photos_dir.expanduser().resolve()),
        "album_count": len(albums),
        "media_count": media_count,
        "last_ingest": data.get("last_ingest"),
        "albums": [
            {
                "slug": album.slug,
                "title": album.title,
                "media_count": album.media_count,
                "path": album.path,
            }
            for album in albums
        ],
    }


def newest_takeout_archive(takeout_dir: Path, *, since_epoch: float | None = None) -> Path | None:
    if not takeout_dir.is_dir():
        return None
    newest: Path | None = None
    newest_mtime = 0.0
    for path in takeout_dir.iterdir():
        if not path.is_file() or path.suffix.lower() != ".zip":
            continue
        mtime = path.stat().st_mtime
        if since_epoch is not None and mtime <= since_epoch:
            continue
        if mtime > newest_mtime:
            newest = path
            newest_mtime = mtime
    return newest


def wait_for_takeout_archive(
    takeout_dir: Path,
    *,
    timeout: int = 120,
    interval: float = 1.0,
    since_epoch: float | None = None,
) -> Path:
    if not takeout_dir.is_dir():
        raise FileNotFoundError(f"Takeout directory not found: {takeout_dir}")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        found = newest_takeout_archive(takeout_dir, since_epoch=since_epoch)
        if found:
            return found
        time.sleep(interval)
    raise TimeoutError(f"Timed out after {timeout}s waiting for Takeout .zip in {takeout_dir}")


def _find_google_photos_root(root: Path) -> Path | None:
    root = root.expanduser().resolve()
    for name in _GOOGLE_PHOTOS_NAMES:
        candidate = root / name
        if candidate.is_dir():
            return candidate
    for path in root.rglob("*"):
        if path.is_dir() and path.name in _GOOGLE_PHOTOS_NAMES and len(path.relative_to(root).parts) <= 4:
            return path
    return None


def _album_dirs(google_photos_root: Path) -> list[tuple[str, Path]]:
    albums: list[tuple[str, Path]] = []
    for path in sorted(google_photos_root.iterdir()):
        if path.is_dir():
            albums.append((path.name, path))
    return albums


def _copy_album_media(src_album: Path, dest_album: Path, *, dry_run: bool) -> int:
    count = 0
    for path in sorted(src_album.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in _MEDIA_SUFFIXES:
            continue
        rel = path.relative_to(src_album)
        target = dest_album / rel
        count += 1
        if dry_run:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    return count


def _materialize_takeout(source: Path) -> tuple[Path, Path | None]:
    source = source.expanduser().resolve()
    if source.is_dir():
        return source, None
    if not source.is_file() or source.suffix.lower() != ".zip":
        raise FileNotFoundError(f"Takeout source not found: {source}")
    tmp_dir = Path(tempfile.mkdtemp(prefix="cli-photos-takeout-"))
    with zipfile.ZipFile(source) as archive:
        archive.extractall(tmp_dir)
    return tmp_dir, tmp_dir


def ingest_takeout(
    photos_dir: Path,
    takeout_dir: Path,
    *,
    source: Path | None = None,
    dry_run: bool = False,
    timeout: int = 120,
    interval: float = 1.0,
    since_epoch: float | None = None,
) -> IngestResult:
    """Import album media from a Google Takeout zip or directory into photos_dir."""

    photos_dir = photos_dir.expanduser().resolve()
    takeout_dir = takeout_dir.expanduser().resolve()
    if source is None:
        source_path = wait_for_takeout_archive(
            takeout_dir,
            timeout=timeout,
            interval=interval,
            since_epoch=since_epoch,
        )
    else:
        source_path = source.expanduser().resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Takeout source not found: {source_path}")

    materialized, cleanup = _materialize_takeout(source_path)
    try:
        google_root = _find_google_photos_root(materialized)
        if google_root is None:
            raise FileNotFoundError(
                f"No 'Google Photos' directory in Takeout export: {source_path}"
            )
        result = IngestResult(source=str(source_path), dry_run=dry_run)
        albums_root = photos_dir / ALBUMS_DIR
        if not dry_run:
            albums_root.mkdir(parents=True, exist_ok=True)

        merged: dict[str, AlbumRecord] = {album.slug: album for album in list_albums(photos_dir)}
        for title, album_src in _album_dirs(google_root):
            slug = _slugify(title)
            dest_album = albums_root / slug
            copied = _copy_album_media(album_src, dest_album, dry_run=dry_run)
            if copied == 0:
                continue
            result.albums.append(slug)
            result.media_files += copied
            existing = merged.get(slug)
            media_count = (existing.media_count if existing else 0) + copied
            merged[slug] = AlbumRecord(
                slug=slug,
                title=title,
                media_count=media_count,
                path=f"{ALBUMS_DIR}/{slug}",
            )

        if not dry_run and merged:
            write_manifest(photos_dir, list(merged.values()))
        return result
    finally:
        if cleanup is not None:
            shutil.rmtree(cleanup, ignore_errors=True)
