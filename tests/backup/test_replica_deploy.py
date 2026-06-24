"""Replica deploy (USB copy and cloud fallback)."""

from __future__ import annotations

from tests.constants import ROOT

from pathlib import Path

from src.services.replica_deploy import deploy_usb_replica, resolve_deploy_replicas
from src.utils.config import BackupReplica


def test_deploy_usb_replica_copies_missing(tmp_path: Path) -> None:
    local = tmp_path / "tags"
    (local / "demo-repo").mkdir(parents=True)
    (local / "demo-repo" / "demo-repo-v1.zip").write_bytes(b"zip-bytes")
    usb = tmp_path / "usb"
    replica = BackupReplica(type="usb", path=str(usb), name="usb-test")

    first = deploy_usb_replica(local, replica)
    assert first.uploaded == ["demo-repo/demo-repo-v1.zip"]
    assert (usb / "demo-repo" / "demo-repo-v1.zip").read_bytes() == b"zip-bytes"

    second = deploy_usb_replica(local, replica)
    assert second.skipped == ["demo-repo/demo-repo-v1.zip"]
    assert second.uploaded == []


def test_resolve_deploy_replicas_from_config(tmp_path: Path) -> None:
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text(
        "backup:\n"
        "  replicas:\n"
        "    - type: usb\n"
        f"      path: {tmp_path / 'vol'}\n",
        encoding="utf-8",
    )
    rows = resolve_deploy_replicas(cfg_dir)
    assert len(rows) == 1
    assert rows[0].type == "usb"
