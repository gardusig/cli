"""Unit tests for Google Drive provider (mocked HTTP)."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from src.providers import google_drive
from src.providers.drive_http import DriveApiError
from src.utils.http import default_http_timeout


def _is_files_list(request: httpx.Request) -> bool:
    return request.method == "GET" and request.url.path.endswith("/files") and "alt=media" not in str(
        request.url
    )


def _mock_client(handler) -> httpx.Client:
    return httpx.Client(
        base_url=google_drive._BASE_URL,
        transport=httpx.MockTransport(handler),
        headers={"Authorization": "Bearer test-token"},
        timeout=default_http_timeout(),
    )


def test_google_list_files_empty_root(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if _is_files_list(request):
            return httpx.Response(
                200,
                json={"files": [{"id": "f1", "name": "a.zip", "mimeType": "text/plain"}]},
            )
        raise AssertionError(str(request.url))

    monkeypatch.setattr(google_drive, "require_google_drive_token", lambda *a, **k: "t")
    monkeypatch.setattr(google_drive, "_client", lambda: _mock_client(handler))
    assert google_drive.list_files("") == {"a.zip"}


def _root_listing(request: httpx.Request) -> bool:
    q = request.url.params.get("q", "")
    return "'root' in parents" in q


def test_google_exists_true(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if _is_files_list(request):
            q = request.url.params.get("q", "")
            if _root_listing(request):
                return httpx.Response(
                    200,
                    json={
                        "files": [
                            {
                                "id": "folder",
                                "name": "repo",
                                "mimeType": google_drive._FOLDER_MIME,
                            }
                        ]
                    },
                )
            if "'folder'" in q:
                return httpx.Response(
                    200,
                    json={
                        "files": [
                            {"id": "f1", "name": "tag.zip", "mimeType": "text/plain"},
                        ]
                    },
                )
            return httpx.Response(200, json={"files": []})
        raise AssertionError(str(request.url))

    monkeypatch.setattr(google_drive, "require_google_drive_token", lambda *a, **k: "t")
    monkeypatch.setattr(google_drive, "_client", lambda: _mock_client(handler))
    assert google_drive.exists("repo/tag.zip") is True


def test_google_upload_skips_existing(monkeypatch, tmp_path: Path) -> None:
    local = tmp_path / "tag.zip"
    local.write_bytes(b"zip")

    def handler(request: httpx.Request) -> httpx.Response:
        if _is_files_list(request):
            q = request.url.params.get("q", "")
            if _root_listing(request):
                return httpx.Response(
                    200,
                    json={
                        "files": [
                            {
                                "id": "folder",
                                "name": "repo",
                                "mimeType": google_drive._FOLDER_MIME,
                            }
                        ]
                    },
                )
            if "'folder'" in q:
                return httpx.Response(
                    200,
                    json={"files": [{"id": "f1", "name": "tag.zip", "mimeType": "text/plain"}]},
                )
            return httpx.Response(200, json={"files": []})
        if request.method == "POST" and request.url.path.endswith("/files"):
            raise AssertionError("upload should be skipped when file exists")
        raise AssertionError(str(request.url))

    monkeypatch.setattr(google_drive, "require_google_drive_token", lambda *a, **k: "t")
    monkeypatch.setattr(google_drive, "_client", lambda: _mock_client(handler))
    google_drive.upload(local, "repo/tag.zip")


def test_google_upload_creates_file(monkeypatch, tmp_path: Path) -> None:
    local = tmp_path / "tag.zip"
    local.write_bytes(b"zip")
    posted = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal posted
        if _is_files_list(request):
            return httpx.Response(200, json={"files": []})
        if request.method == "POST" and "uploadType=multipart" in str(request.url):
            posted = True
            return httpx.Response(200, json={"id": "new"})
        if request.method == "POST" and request.url.path.endswith("/files"):
            return httpx.Response(200, json={"id": "folder"})
        raise AssertionError(str(request.url))

    monkeypatch.setattr(google_drive, "require_google_drive_token", lambda *a, **k: "t")
    monkeypatch.setattr(google_drive, "_client", lambda: _mock_client(handler))
    google_drive.upload(local, "repo/tag.zip")
    assert posted


def test_google_download_writes_local(monkeypatch, tmp_path: Path) -> None:
    dest = tmp_path / "out" / "tag.zip"

    def handler(request: httpx.Request) -> httpx.Response:
        if _is_files_list(request):
            q = request.url.params.get("q", "")
            if _root_listing(request):
                return httpx.Response(
                    200,
                    json={
                        "files": [
                            {
                                "id": "folder",
                                "name": "repo",
                                "mimeType": google_drive._FOLDER_MIME,
                            }
                        ]
                    },
                )
            if "'folder'" in q:
                return httpx.Response(
                    200,
                    json={"files": [{"id": "f1", "name": "tag.zip", "mimeType": "text/plain"}]},
                )
            return httpx.Response(200, json={"files": []})
        if request.url.path.endswith("/files/f1"):
            return httpx.Response(200, content=b"payload")
        raise AssertionError(str(request.url))

    monkeypatch.setattr(google_drive, "require_google_drive_token", lambda *a, **k: "t")
    monkeypatch.setattr(google_drive, "_client", lambda: _mock_client(handler))
    google_drive.download("repo/tag.zip", str(dest))
    assert dest.read_bytes() == b"payload"


def test_google_missing_token(monkeypatch) -> None:
    monkeypatch.setattr(
        google_drive,
        "require_google_drive_token",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("GOOGLE_DRIVE_TOKEN is not set")),
    )
    with pytest.raises(RuntimeError, match="GOOGLE_DRIVE_TOKEN"):
        google_drive.list_files("git-tags")


def test_google_api_error_retryable_flag() -> None:
    err = DriveApiError("rate limited", status_code=429, retryable=True)
    assert err.retryable is True
