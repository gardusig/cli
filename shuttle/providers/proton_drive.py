"""Proton Drive provider adapter."""

from __future__ import annotations

from pathlib import Path

name = "proton"


def list_files(_root: str) -> set[str]:
    raise NotImplementedError("Proton Drive list_files not implemented yet")


def exists(_path: str) -> bool:
    raise NotImplementedError("Proton Drive exists not implemented yet")


def create_directory(_path: str) -> None:
    raise NotImplementedError("Proton Drive create_directory not implemented yet")


def upload(_local: Path, _remote: str) -> None:
    raise NotImplementedError("Proton Drive upload not implemented yet")


def download(_remote_path: str, _local_path: str) -> None:
    raise NotImplementedError("Proton Drive download not implemented yet")


def delete(_remote_path: str) -> None:
    raise NotImplementedError("Proton Drive delete not implemented yet")
