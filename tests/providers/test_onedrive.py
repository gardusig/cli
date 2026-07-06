"""Unit tests for OneDrive provider (mocked HTTP)."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from src.providers import onedrive
from src.utils.http import default_http_timeout


def _mock_client(handler) -> httpx.Client:
    return httpx.Client(
        base_url=onedrive._BASE_URL,
        transport=httpx.MockTransport(handler),
        headers={"Authorization": "Bearer test-token"},
        timeout=default_http_timeout(),
    )


def test_onedrive_list_files(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/children"):
            if "nested" in path:
                return httpx.Response(200, json={"value": [{"name": "inner.zip", "file": {}}]})
            return httpx.Response(
                200,
                json={
                    "value": [
                        {"name": "demo.zip", "file": {}},
                        {"name": "nested", "folder": {}},
                    ]
                },
            )
        if "git-tags" in path and request.method == "GET":
            return httpx.Response(200, json={"id": "root"})
        return httpx.Response(404)

    monkeypatch.setattr(onedrive, "require_onedrive_token", lambda *a, **k: "t")
    monkeypatch.setattr(onedrive, "_client", lambda: _mock_client(handler))
    files = onedrive.list_files("git-tags")
    assert "demo.zip" in files
    assert "nested/inner.zip" in files


def test_onedrive_exists(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and "demo.zip" in request.url.path:
            return httpx.Response(200, json={"id": "item"})
        return httpx.Response(404)

    monkeypatch.setattr(onedrive, "require_onedrive_token", lambda *a, **k: "t")
    monkeypatch.setattr(onedrive, "_client", lambda: _mock_client(handler))
    assert onedrive.exists("git-tags/demo.zip") is True
    assert onedrive.exists("git-tags/missing.zip") is False


def test_onedrive_upload(monkeypatch, tmp_path: Path) -> None:
    local = tmp_path / "demo.zip"
    local.write_bytes(b"z")
    put_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "PUT" and ":/content" in request.url.path:
            put_paths.append(request.url.path)
            return httpx.Response(200, json={"id": "new"})
        if request.method == "GET":
            return httpx.Response(404)
        if request.method == "POST":
            return httpx.Response(201, json={"id": "folder"})
        raise AssertionError(str(request.url))

    monkeypatch.setattr(onedrive, "require_onedrive_token", lambda *a, **k: "t")
    monkeypatch.setattr(onedrive, "_client", lambda: _mock_client(handler))
    onedrive.upload(local, "git-tags/demo.zip")
    assert put_paths


def test_onedrive_download(monkeypatch, tmp_path: Path) -> None:
    dest = tmp_path / "demo.zip"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith(":/content") and request.method == "GET":
            return httpx.Response(200, content=b"data")
        if request.method == "GET":
            return httpx.Response(200, json={"id": "item"})
        return httpx.Response(404)

    monkeypatch.setattr(onedrive, "require_onedrive_token", lambda *a, **k: "t")
    monkeypatch.setattr(onedrive, "_client", lambda: _mock_client(handler))
    onedrive.download("git-tags/demo.zip", str(dest))
    assert dest.read_bytes() == b"data"


def test_onedrive_missing_token(monkeypatch) -> None:
    monkeypatch.setattr(
        onedrive,
        "require_onedrive_token",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("ONEDRIVE_TOKEN is not set")),
    )
    with pytest.raises(RuntimeError, match="ONEDRIVE_TOKEN"):
        onedrive.list_files("git-tags")
