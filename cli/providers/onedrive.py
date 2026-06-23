"""Microsoft OneDrive provider adapter."""

from __future__ import annotations

from pathlib import Path

name = "onedrive"


def list_files(_root: str) -> set[str]:
    raise NotImplementedError("OneDrive list_files not implemented yet")


def exists(_path: str) -> bool:
    raise NotImplementedError("OneDrive exists not implemented yet")


def create_directory(_path: str) -> None:
    raise NotImplementedError("OneDrive create_directory not implemented yet")


def upload(_local: Path, _remote: str) -> None:
    raise NotImplementedError("OneDrive upload not implemented yet")


def download(_remote_path: str, _local_path: str) -> None:
    raise NotImplementedError("OneDrive download not implemented yet")


def delete(_remote_path: str) -> None:
    raise NotImplementedError("OneDrive delete not implemented yet")
