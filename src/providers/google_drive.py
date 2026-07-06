"""Google Drive provider adapter (Drive API v3)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx

from src.providers.drive_http import (
    DriveApiError,
    bearer_client,
    join_remote_path,
    raise_for_status,
    read_local_bytes,
    split_remote_path,
)
from src.utils.config import require_google_drive_token

name = "google"

_FOLDER_MIME = "application/vnd.google-apps.folder"
_BASE_URL = "https://www.googleapis.com/drive/v3"


def _client() -> httpx.Client:
    return bearer_client(require_google_drive_token(), base_url=_BASE_URL)


def _list_children(client: httpx.Client, parent_id: str) -> list[dict]:
    files: list[dict] = []
    page_token: str | None = None
    while True:
        params: dict[str, str] = {
            "q": f"'{parent_id}' in parents and trashed=false",
            "fields": "nextPageToken, files(id, name, mimeType)",
            "pageSize": "200",
        }
        if page_token:
            params["pageToken"] = page_token
        response = client.get("/files", params=params)
        raise_for_status(response, operation="google drive list children")
        payload = response.json()
        files.extend(payload.get("files", []))
        page_token = payload.get("nextPageToken")
        if not page_token:
            break
    return files


def _find_child_folder(client: httpx.Client, parent_id: str, folder_name: str) -> str | None:
    for item in _list_children(client, parent_id):
        if item.get("mimeType") == _FOLDER_MIME and item.get("name") == folder_name:
            return str(item["id"])
    return None


def _create_folder(client: httpx.Client, parent_id: str, folder_name: str) -> str:
    response = client.post(
        "/files",
        json={
            "name": folder_name,
            "mimeType": _FOLDER_MIME,
            "parents": [parent_id],
        },
    )
    raise_for_status(response, operation="google drive create folder")
    return str(response.json()["id"])


def _ensure_folder_id(client: httpx.Client, remote_path: str) -> str:
    parent, leaf = split_remote_path(remote_path)
    folder_id = "root"
    if parent:
        for segment in parent.split("/"):
            if not segment:
                continue
            existing = _find_child_folder(client, folder_id, segment)
            if existing:
                folder_id = existing
            else:
                folder_id = _create_folder(client, folder_id, segment)
    if not leaf:
        return folder_id
    existing = _find_child_folder(client, folder_id, leaf)
    if existing:
        return existing
    return _create_folder(client, folder_id, leaf)


def _file_id_by_path(client: httpx.Client, remote_path: str) -> str | None:
    parent_path, file_name = split_remote_path(remote_path)
    if not file_name:
        return None
    parent_id = _ensure_folder_id(client, parent_path) if parent_path else "root"
    for item in _list_children(client, parent_id):
        if item.get("mimeType") != _FOLDER_MIME and item.get("name") == file_name:
            return str(item["id"])
    return None


def _walk_files(client: httpx.Client, folder_id: str, prefix: str) -> set[str]:
    rels: set[str] = set()
    for item in _list_children(client, folder_id):
        item_name = str(item.get("name", ""))
        rel = f"{prefix}/{item_name}" if prefix else item_name
        if item.get("mimeType") == _FOLDER_MIME:
            rels.update(_walk_files(client, str(item["id"]), rel))
        else:
            rels.add(rel)
    return rels


def list_files(root: str) -> set[str]:
    root = root.strip("/")
    with _client() as client:
        if not root:
            return _walk_files(client, "root", "")
        folder_id = _ensure_folder_id(client, root)
        return _walk_files(client, folder_id, "")


def exists(path: str) -> bool:
    path = path.strip("/")
    if not path:
        return False
    with _client() as client:
        return _file_id_by_path(client, path) is not None


def create_directory(path: str) -> None:
    path = path.strip("/")
    if not path:
        return
    with _client() as client:
        _ensure_folder_id(client, path)


def upload(local: Path, remote: str) -> None:
    remote = remote.strip("/")
    parent_path, file_name = split_remote_path(remote)
    if not file_name:
        raise DriveApiError(f"invalid remote upload path: {remote!r}")
    with _client() as client:
        parent_id = _ensure_folder_id(client, parent_path) if parent_path else "root"
        existing = _file_id_by_path(client, remote)
        if existing:
            return
        metadata = {"name": file_name, "parents": [parent_id]}
        response = client.post(
            "/files",
            params={"uploadType": "multipart"},
            files={
                "metadata": ("metadata", json.dumps(metadata), "application/json"),
                "file": (file_name, read_local_bytes(local), "application/octet-stream"),
            },
        )
        raise_for_status(response, operation="google drive upload")


def download(remote_path: str, local_path: str) -> None:
    remote_path = remote_path.strip("/")
    with _client() as client:
        file_id = _file_id_by_path(client, remote_path)
        if not file_id:
            raise DriveApiError(f"remote file not found: {remote_path}")
        response = client.get(f"/files/{file_id}", params={"alt": "media"})
        raise_for_status(response, operation="google drive download")
        dest = Path(local_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(response.content)


def delete(_remote_path: str) -> None:
    raise NotImplementedError("Google Drive delete not implemented (append-only policy)")
