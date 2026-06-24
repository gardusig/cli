"""Deploy local git-tags zips to configured replicas (cloud drives or USB paths)."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Literal

from cli.providers import google_drive, onedrive, proton_drive
from cli.providers.base import DriveProvider
from cli.services.drive_sync import UploadResult, upload_missing
from cli.utils.config import BackupReplica, load_config

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


def deploy_usb_replica(local_root: Path, replica: BackupReplica) -> UploadResult:
    """Copy missing or changed zips from local hub to a USB (or other) mount path."""
    if not replica.path.strip():
        raise RuntimeError("usb replica requires backup.replicas[].path")
    dest_root = Path(replica.path).expanduser().resolve()
    dest_root.mkdir(parents=True, exist_ok=True)
    result = UploadResult()
    if not local_root.is_dir():
        return result

    for path in sorted(local_root.rglob("*.zip")):
        if not path.is_file():
            continue
        rel = path.relative_to(local_root).as_posix()
        target = dest_root / rel
        if target.is_file() and target.stat().st_size == path.stat().st_size:
            result.skipped.append(rel)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        result.uploaded.append(rel)
    return result


def deploy_cloud_replica(local_root: Path, replica: BackupReplica) -> UploadResult:
    provider_name = replica.provider.strip()
    if provider_name not in _PROVIDER_MODULES:
        raise RuntimeError(f"Unknown cloud provider for replica: {provider_name!r}")
    remote_root = replica.root.strip() or "git-tags"
    return upload_missing(local_root, _PROVIDER_MODULES[provider_name], remote_root)


def deploy_replicas(
    local_root: Path,
    *,
    config_dir: Path | None = None,
    selected: str | None = None,
    kinds: tuple[ReplicaKind, ...] | None = None,
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
        if replica.type == "usb":
            rows.append((label, deploy_usb_replica(local_root, replica)))
        else:
            rows.append((label, deploy_cloud_replica(local_root, replica)))
    return rows
