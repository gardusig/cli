"""One-way upload of missing local files to cloud drive providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from shuttle.providers.base import DriveProvider
from shuttle.providers.drive_client import wrap_drive_provider
from shuttle.services.backup_repository import SyncResult, ingest_repositories
from shuttle.utils.external_client import ExternalCallError


@dataclass
class UploadResult:
    uploaded: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
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
) -> UploadResult:
    """Upload files present locally but missing remotely (append-only)."""
    remote = wrap_drive_provider(provider)
    result = UploadResult()
    remote_root = remote_root.strip("/")
    local_files = _scan_local_files(local_root)
    try:
        remote_files = remote.list_files(remote_root)
    except NotImplementedError:
        raise
    except ExternalCallError:
        raise
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
            try:
                remote.create_directory(parent)
            except NotImplementedError:
                raise
            except ExternalCallError:
                raise
            except Exception as exc:  # noqa: BLE001
                result.failed.append((rel, f"mkdir: {exc}"))
                continue
        try:
            remote.upload(local_path, remote_path)
            result.uploaded.append(rel)
        except NotImplementedError:
            raise
        except ExternalCallError:
            raise
        except Exception as exc:  # noqa: BLE001
            result.failed.append((rel, str(exc)))
    return result


@dataclass
class DriveSyncResult:
    """Ingest all configured repos, then upload missing zips to each provider."""

    ingest: list[tuple[Path, SyncResult]] = field(default_factory=list)
    uploads: list[tuple[str, UploadResult]] = field(default_factory=list)


def sync_all(
    local_root: Path,
    providers: list[tuple[str, DriveProvider, str]],
    *,
    ingest_path: str | None = None,
) -> DriveSyncResult:
    """Zip tags for configured repositories, then push missing files to cloud."""
    ingest_rows = ingest_repositories(ingest_path)
    uploads: list[tuple[str, UploadResult]] = []
    if local_root.is_dir():
        for name, module, remote_root in providers:
            uploads.append((name, upload_missing(local_root, module, remote_root)))
    return DriveSyncResult(ingest=ingest_rows, uploads=uploads)


def upload_backup(_local_path: str, _drive: str) -> None:
    raise NotImplementedError("Use shuttle drive upload instead")


def download_latest(_drive: str, _dest: str) -> None:
    raise NotImplementedError("Drive download not implemented yet")
