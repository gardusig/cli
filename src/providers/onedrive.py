"""Microsoft OneDrive provider adapter (Microsoft Graph)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx

from src.providers.drive_http import (
    DriveApiError,
    bearer_client,
    raise_for_status,
    read_local_bytes,
    split_remote_path,
)
from src.utils.config import require_onedrive_token

name = "onedrive"

_BASE_URL = "https://graph.microsoft.com/v1.0"


def _client() -> httpx.Client:
    return bearer_client(require_onedrive_token(), base_url=_BASE_URL)


def _item_path(remote_path: str) -> str:
    cleaned = remote_path.strip("/").replace("\\", "/")
    if not cleaned:
        return "/me/drive/root"
    return f"/me/drive/root:/{cleaned}"


def _children_path(remote_path: str) -> str:
    base = _item_path(remote_path)
    if base.endswith("/root"):
        return f"{base}/children"
    return f"{base}:/children"


def _list_children(client: httpx.Client, remote_path: str) -> list[dict]:
    items: list[dict] = []
    url = _children_path(remote_path)
    while url:
        response = client.get(url)
        raise_for_status(response, operation="onedrive list children")
        payload = response.json()
        items.extend(payload.get("value", []))
        url = payload.get("@odata.nextLink")
        if url and url.startswith(_BASE_URL):
            url = url[len(_BASE_URL) :]
    return items


def _item_exists(client: httpx.Client, remote_path: str) -> bool:
    response = client.get(_item_path(remote_path))
    if response.status_code == 404:
        return False
    raise_for_status(response, operation="onedrive get item")
    return True


def _create_folder(client: httpx.Client, parent_path: str, folder_name: str) -> None:
    response = client.post(
        _children_path(parent_path),
        json={
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail",
        },
    )
    if response.status_code == 409:
        return
    raise_for_status(response, operation="onedrive create folder")


def _ensure_path(client: httpx.Client, remote_path: str) -> None:
    cleaned = remote_path.strip("/")
    if not cleaned:
        return
    parent, leaf = split_remote_path(cleaned)
    if parent:
        _ensure_path(client, parent)
        if not _item_exists(client, cleaned):
            _create_folder(client, parent, leaf)
    elif not _item_exists(client, leaf):
        _create_folder(client, "", leaf)


def _walk_files(client: httpx.Client, remote_path: str, prefix: str) -> set[str]:
    rels: set[str] = set()
    for item in _list_children(client, remote_path):
        item_name = str(item.get("name", ""))
        rel = f"{prefix}/{item_name}" if prefix else item_name
        if item.get("folder") is not None:
            child_path = f"{remote_path}/{item_name}".strip("/") if remote_path else item_name
            rels.update(_walk_files(client, child_path, rel))
        else:
            rels.add(rel)
    return rels


def list_files(root: str) -> set[str]:
    root = root.strip("/")
    with _client() as client:
        if root and not _item_exists(client, root):
            return set()
        return _walk_files(client, root, "")


def exists(path: str) -> bool:
    path = path.strip("/")
    if not path:
        return False
    with _client() as client:
        return _item_exists(client, path)


def create_directory(path: str) -> None:
    path = path.strip("/")
    if not path:
        return
    with _client() as client:
        _ensure_path(client, path)


def upload(local: Path, remote: str) -> None:
    remote = remote.strip("/")
    if not remote:
        raise DriveApiError("invalid remote upload path")
    with _client() as client:
        parent_path, _ = split_remote_path(remote)
        if parent_path:
            _ensure_path(client, parent_path)
        if _item_exists(client, remote):
            return
        response = client.put(
            f"{_item_path(remote)}:/content",
            content=read_local_bytes(local),
            headers={"Content-Type": "application/octet-stream"},
        )
        raise_for_status(response, operation="onedrive upload")


def download(remote_path: str, local_path: str) -> None:
    remote_path = remote_path.strip("/")
    with _client() as client:
        if not _item_exists(client, remote_path):
            raise DriveApiError(f"remote file not found: {remote_path}")
        response = client.get(f"{_item_path(remote_path)}:/content")
        raise_for_status(response, operation="onedrive download")
        dest = Path(local_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(response.content)


def delete(_remote_path: str) -> None:
    raise NotImplementedError("OneDrive delete not implemented (append-only policy)")
