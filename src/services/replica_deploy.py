"""Deploy local git-tags zips to configured replicas (cloud drives or USB paths)."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Literal

from src.providers import google_drive, onedrive, proton_drive
from src.providers.base import DriveProvider
from src.providers.proton_drive import ProtonDriveUnsupportedError
from src.services.drive_sync import (
    DownloadResult,
    ReplicaPreflight,
    UploadResult,
    download_missing,
    replica_preflight,
    upload_missing,
)
from src.utils.config import BackupReplica, load_config
from src.utils.external_client import ExternalCallError

ReplicaKind = Literal["cloud", "usb"]

_PROVIDER_MODULES: dict[str, DriveProvider] = {
    "google": google_drive,
    "onedrive": onedrive,
    "proton": proton_drive,
}


def _replica_label(replica: BackupReplica) -> str:
    if replica.name.strip():
        return replica.name.strip()
    if replica.type == "usb":
        return f"usb:{replica.path}"
    return replica.provider or "cloud"


def resolve_deploy_replicas(config_dir: Path | None = None) -> list[BackupReplica]:
    """Return explicit backup.replicas, or synthesize from enabled drives.yaml providers."""
    cfg = load_config(config_dir)
    if cfg.backup.replicas:
        return list(cfg.backup.replicas)

    rows: list[BackupReplica] = []
    for name, pcfg in (
        ("google", cfg.drives.google),
        ("onedrive", cfg.drives.onedrive),
        ("proton", cfg.drives.proton),
    ):
        if pcfg.enabled and pcfg.root:
            rows.append(
                BackupReplica(
                    type="cloud",
                    provider=name,
                    root=pcfg.root,
                    name=name,
                )
            )
    return rows


def deploy_usb_replica(
    local_root: Path,
    replica: BackupReplica,
    *,
    dry_run: bool = False,
) -> UploadResult:
    """Copy missing or changed zips from local hub to a USB (or other) mount path."""
    if not replica.path.strip():
        raise RuntimeError("usb replica requires backup.replicas[].path")
    dest_root = Path(replica.path).expanduser().resolve()
    result = UploadResult(dry_run=dry_run)
    if not local_root.is_dir():
        return result
    if not dry_run:
        dest_root.mkdir(parents=True, exist_ok=True)

    for path in sorted(local_root.rglob("*.zip")):
        if not path.is_file():
            continue
        rel = path.relative_to(local_root).as_posix()
        target = dest_root / rel
        if target.is_file() and target.stat().st_size == path.stat().st_size:
            result.skipped.append(rel)
            continue
        if dry_run:
            result.uploaded.append(rel)
            continue
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            result.uploaded.append(rel)
        except OSError as exc:
            result.failed.append((rel, str(exc)))
    return result


def deploy_cloud_replica(
    local_root: Path,
    replica: BackupReplica,
    *,
    dry_run: bool = False,
) -> UploadResult:
    provider_name = replica.provider.strip()
    if provider_name not in _PROVIDER_MODULES:
        raise RuntimeError(f"Unknown cloud provider for replica: {provider_name!r}")
    remote_root = replica.root.strip() or "git-tags"
    return upload_missing(
        local_root,
        _PROVIDER_MODULES[provider_name],
        remote_root,
        dry_run=dry_run,
    )


def download_cloud_replica(
    local_root: Path,
    replica: BackupReplica,
    *,
    dry_run: bool = False,
    force: bool = False,
) -> DownloadResult:
    provider_name = replica.provider.strip()
    if provider_name not in _PROVIDER_MODULES:
        raise RuntimeError(f"Unknown cloud provider for replica: {provider_name!r}")
    if provider_name == "proton":
        result = DownloadResult(dry_run=dry_run)
        try:
            proton_drive.list_files("")
        except ProtonDriveUnsupportedError as exc:
            result.failed = [("", str(exc))]
        return result
    remote_root = replica.root.strip() or "git-tags"
    return download_missing(
        local_root,
        _PROVIDER_MODULES[provider_name],
        remote_root,
        dry_run=dry_run,
        force=force,
    )


def preflight_replicas(
    local_root: Path,
    *,
    config_dir: Path | None = None,
    selected: str | None = None,
    kinds: tuple[ReplicaKind, ...] | None = None,
) -> list[ReplicaPreflight]:
    replicas = resolve_deploy_replicas(config_dir)
    if kinds:
        replicas = [r for r in replicas if r.type in kinds]
    if not replicas:
        raise RuntimeError(
            "No backup replicas configured. Add backup.replicas in config.yaml "
            "or enable providers in drives.yaml."
        )
    if selected:
        key = selected.casefold()
        matches = [
            r
            for r in replicas
            if key
            in {
                _replica_label(r).casefold(),
                r.provider.casefold(),
                r.name.casefold(),
                r.path.casefold(),
            }
        ]
        if not matches:
            raise RuntimeError(f"No replica matches: {selected!r}")
        replicas = matches

    rows: list[ReplicaPreflight] = []
    for replica in replicas:
        label = _replica_label(replica)
        if replica.type == "usb":
            local_files = list(local_root.rglob("*.zip")) if local_root.is_dir() else []
            dest_root = Path(replica.path).expanduser()
            remote_count = (
                len(list(dest_root.rglob("*.zip"))) if dest_root.is_dir() else 0
            )
            local_rels = {
                p.relative_to(local_root).as_posix()
                for p in local_files
                if p.is_file()
            }
            rows.append(
                ReplicaPreflight(
                    name=label,
                    local_count=len(local_rels),
                    remote_count=remote_count,
                )
            )
            continue
        provider_name = replica.provider.strip()
        module = _PROVIDER_MODULES.get(provider_name)
        if module is None:
            rows.append(
                ReplicaPreflight(
                    name=label,
                    local_count=0,
                    remote_count=0,
                    failed=[("", f"unknown provider: {provider_name!r}")],
                )
            )
            continue
        rows.append(
            replica_preflight(
                local_root,
                module,
                replica.root.strip() or "git-tags",
                name=label,
            )
        )
    return rows


def deploy_replicas(
    local_root: Path,
    *,
    config_dir: Path | None = None,
    selected: str | None = None,
    kinds: tuple[ReplicaKind, ...] | None = None,
    dry_run: bool = False,
) -> list[tuple[str, UploadResult]]:
    """Deploy local tag zips to every configured replica (or one by label/provider)."""
    replicas = resolve_deploy_replicas(config_dir)
    if kinds:
        replicas = [r for r in replicas if r.type in kinds]
    if not replicas:
        raise RuntimeError(
            "No backup replicas configured. Add backup.replicas in config.yaml "
            "or enable providers in drives.yaml."
        )

    if selected:
        key = selected.casefold()
        matches = [
            r
            for r in replicas
            if key
            in {
                _replica_label(r).casefold(),
                r.provider.casefold(),
                r.name.casefold(),
                r.path.casefold(),
            }
        ]
        if not matches:
            raise RuntimeError(f"No replica matches: {selected!r}")
        replicas = matches

    rows: list[tuple[str, UploadResult]] = []
    for replica in replicas:
        label = _replica_label(replica)
        try:
            if replica.type == "usb":
                rows.append(
                    (label, deploy_usb_replica(local_root, replica, dry_run=dry_run))
                )
            else:
                rows.append(
                    (label, deploy_cloud_replica(local_root, replica, dry_run=dry_run))
                )
        except NotImplementedError as exc:
            rows.append((label, UploadResult(failed=[("", str(exc))], dry_run=dry_run)))
        except (ProtonDriveUnsupportedError, RuntimeError, ExternalCallError) as exc:
            message = getattr(exc, "user_message", str(exc))
            rows.append((label, UploadResult(failed=[("", message)], dry_run=dry_run)))
    return rows


def download_replicas(
    local_root: Path,
    *,
    config_dir: Path | None = None,
    selected: str | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> list[tuple[str, DownloadResult]]:
    """Download missing remote zips into the local git-tags hub (cloud replicas only)."""
    replicas = [r for r in resolve_deploy_replicas(config_dir) if r.type == "cloud"]
    if not replicas:
        raise RuntimeError("No cloud replicas configured for download.")
    if selected:
        key = selected.casefold()
        matches = [
            r
            for r in replicas
            if key
            in {
                _replica_label(r).casefold(),
                r.provider.casefold(),
                r.name.casefold(),
            }
        ]
        if not matches:
            raise RuntimeError(f"No cloud replica matches: {selected!r}")
        replicas = matches

    rows: list[tuple[str, DownloadResult]] = []
    for replica in replicas:
        label = _replica_label(replica)
        try:
            rows.append(
                (
                    label,
                    download_cloud_replica(
                        local_root,
                        replica,
                        dry_run=dry_run,
                        force=force,
                    ),
                )
            )
        except NotImplementedError as exc:
            rows.append(
                (label, DownloadResult(failed=[("", str(exc))], dry_run=dry_run))
            )
        except (ProtonDriveUnsupportedError, RuntimeError, ExternalCallError) as exc:
            message = getattr(exc, "user_message", str(exc))
            rows.append(
                (label, DownloadResult(failed=[("", message)], dry_run=dry_run))
            )
    return rows
