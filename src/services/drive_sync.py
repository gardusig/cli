"""One-way upload of missing local files to cloud drive providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from src.providers.base import DriveProvider
from src.providers.drive_client import wrap_drive_provider
from src.services.backup_repository import SyncResult, ingest_repositories, plan_ingest_repositories
from src.utils.external_client import ExternalCallError


@dataclass
class UploadResult:
    uploaded: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)
    dry_run: bool = False


@dataclass
class DownloadResult:
    downloaded: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)
    dry_run: bool = False


@dataclass
class ReplicaPreflight:
    """Read-only remote/local gap summary for one replica."""

    name: str
    local_count: int
    remote_count: int
    missing_remote: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)


def _scan_local_files(local_root: Path) -> list[str]:
    if not local_root.is_dir():
        return []
    paths: list[str] = []
    for path in sorted(local_root.rglob("*")):
        if path.is_file():
            paths.append(path.relative_to(local_root).as_posix())
    return paths


def upload_missing(
    local_root: Path,
    provider: DriveProvider,
    remote_root: str,
    *,
    dry_run: bool = False,
) -> UploadResult:
    """Upload files present locally but missing remotely (append-only)."""
    remote = wrap_drive_provider(provider)
    result = UploadResult(dry_run=dry_run)
    remote_root = remote_root.strip("/")
    local_files = _scan_local_files(local_root)
    try:
        remote_files = set(remote.list_files(remote_root))
    except NotImplementedError:
        raise
    except ExternalCallError as exc:
        result.failed.append(("", exc.user_message))
        return result
    except Exception as exc:  # noqa: BLE001
        result.failed.append(("", str(exc)))
        return result

    for rel in local_files:
        remote_path = f"{remote_root}/{rel}" if remote_root else rel
        if rel in remote_files or remote.exists(remote_path):
            result.skipped.append(rel)
            continue
        local_path = local_root / rel
        parent = str(Path(remote_path).parent).replace("\\", "/")
        if parent and parent != ".":
            if dry_run:
                result.uploaded.append(rel)
                continue
            try:
                remote.create_directory(parent)
            except NotImplementedError:
                raise
            except ExternalCallError as exc:
                result.failed.append((rel, exc.user_message))
                continue
            except Exception as exc:  # noqa: BLE001
                result.failed.append((rel, f"mkdir: {exc}"))
                continue
        if dry_run:
            result.uploaded.append(rel)
            continue
        try:
            remote.upload(local_path, remote_path)
            result.uploaded.append(rel)
        except NotImplementedError:
            raise
        except ExternalCallError as exc:
            result.failed.append((rel, exc.user_message))
        except Exception as exc:  # noqa: BLE001
            result.failed.append((rel, str(exc)))
    return result


def download_missing(
    local_root: Path,
    provider: DriveProvider,
    remote_root: str,
    *,
    dry_run: bool = False,
    force: bool = False,
) -> DownloadResult:
    """Download remote files missing locally (one-way restore; skip existing unless force)."""
    remote = wrap_drive_provider(provider)
    result = DownloadResult(dry_run=dry_run)
    remote_root = remote_root.strip("/")
    local_files = set(_scan_local_files(local_root))
    try:
        remote_files = set(remote.list_files(remote_root))
    except NotImplementedError:
        raise
    except ExternalCallError as exc:
        result.failed.append(("", exc.user_message))
        return result
    except Exception as exc:  # noqa: BLE001
        result.failed.append(("", str(exc)))
        return result

    for rel in sorted(remote_files):
        local_path = local_root / rel
        if rel in local_files and local_path.is_file() and not force:
            result.skipped.append(rel)
            continue
        remote_path = f"{remote_root}/{rel}" if remote_root else rel
        if dry_run:
            result.downloaded.append(rel)
            continue
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            remote.download(remote_path, local_path)
            result.downloaded.append(rel)
        except NotImplementedError:
            raise
        except ExternalCallError as exc:
            result.failed.append((rel, exc.user_message))
        except Exception as exc:  # noqa: BLE001
            result.failed.append((rel, str(exc)))
    return result


def replica_preflight(
    local_root: Path,
    provider: DriveProvider,
    remote_root: str,
    *,
    name: str,
) -> ReplicaPreflight:
    """Compare local zip inventory to remote paths without writing."""
    local_files = set(_scan_local_files(local_root))
    row = ReplicaPreflight(name=name, local_count=len(local_files), remote_count=0)
    remote_root = remote_root.strip("/")
    remote = wrap_drive_provider(provider)
    try:
        remote_files = set(remote.list_files(remote_root))
    except ExternalCallError as exc:
        row.failed.append(("", exc.user_message))
        return row
    except Exception as exc:  # noqa: BLE001
        row.failed.append(("", str(exc)))
        return row
    row.remote_count = len(remote_files)
    row.missing_remote = sorted(local_files - remote_files)
    return row


@dataclass
class DriveSyncResult:
    """Ingest all configured repos, then upload missing zips to each provider."""

    ingest: list[tuple[Path, SyncResult]] = field(default_factory=list)
    uploads: list[tuple[str, UploadResult]] = field(default_factory=list)
    dry_run: bool = False


def sync_all(
    local_root: Path,
    providers: list[tuple[str, DriveProvider, str]],
    *,
    ingest_path: str | None = None,
    dry_run: bool = False,
) -> DriveSyncResult:
    """Zip tags for configured repositories, then push missing files to cloud."""
    if dry_run:
        ingest_rows = plan_ingest_repositories(ingest_path)
    else:
        ingest_rows = ingest_repositories(ingest_path)
    uploads: list[tuple[str, UploadResult]] = []
    if local_root.is_dir():
        for name, module, remote_root in providers:
            uploads.append(
                (name, upload_missing(local_root, module, remote_root, dry_run=dry_run))
            )
    return DriveSyncResult(ingest=ingest_rows, uploads=uploads, dry_run=dry_run)


def upload_backup(_local_path: str, _drive: str) -> None:
    raise NotImplementedError("Use cli drive upload instead")


def download_latest(_drive: str, _dest: str) -> None:
    raise NotImplementedError("Use cli drive download instead")
