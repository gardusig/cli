"""Proton Drive provider adapter (deferred — no stable public upload API)."""

from __future__ import annotations

from pathlib import Path

name = "proton"

_DEFER_MESSAGE = (
    "Proton Drive upload is not supported: Proton does not offer a stable, "
    "documented third-party API for programmatic uploads in this CLI. "
    "Use Google Drive or OneDrive replicas, or a USB replica. "
    "See docs/drive.md#proton-drive."
)


class ProtonDriveUnsupportedError(RuntimeError):
    """Raised when Proton Drive operations are requested."""


def _unsupported() -> None:
    raise ProtonDriveUnsupportedError(_DEFER_MESSAGE)


def list_files(_root: str) -> set[str]:
    _unsupported()


def exists(_path: str) -> bool:
    _unsupported()


def create_directory(_path: str) -> None:
    _unsupported()


def upload(_local: Path, _remote: str) -> None:
    _unsupported()


def download(_remote_path: str, _local_path: str) -> None:
    _unsupported()


def delete(_remote_path: str) -> None:
    raise NotImplementedError("Proton Drive delete not implemented (append-only policy)")
