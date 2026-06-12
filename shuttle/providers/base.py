"""Shared drive provider interface (issue #4)."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class DriveProvider(Protocol):
    name: str

    def list_files(self, root: str) -> set[str]:
        """Return relative file paths under root."""
        ...

    def exists(self, path: str) -> bool:
        ...

    def create_directory(self, path: str) -> None:
        ...

    def upload(self, local: Path, remote: str) -> None:
        ...
