"""Mocked Notion API sync tests."""

from __future__ import annotations

from tests.constants import ROOT

import json
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from gardusig_cli.integration.workspaces import notion_task_fixture_dir
from gardusig_cli.providers.notion import NotionClient
from gardusig_cli.services.notion_sync import cleanup_board, export_tasks, import_tasks
from gardusig_cli.utils.config import NotionConfig
from gardusig_cli.utils.http import default_http_timeout

FIXTURE_ROOT = notion_task_fixture_dir()
NOTION_BASE = "https://api.notion.com/v1"
_REAL_HTTPX_CLIENT = httpx.Client


def _patch_notion_http(handler):
    def _client_factory(**kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        kwargs.setdefault("base_url", NOTION_BASE)
        kwargs.setdefault("timeout", default_http_timeout())
        return _REAL_HTTPX_CLIENT(**kwargs)

    return patch(
        "gardusig_cli.providers.notion.httpx.Client",
        side_effect=_client_factory,
    )


def test_cleanup_board_archives_pages() -> None:
    archived: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path.endswith("/query"):
            return httpx.Response(
                200,
                json={
                    "results": [{"id": "page-1", "archived": False, "properties": {}}],
                    "has_more": False,
                },
            )
        if request.method == "PATCH" and "/pages/" in request.url.path:
            archived.append(request.url.path.split("/")[-1])
            return httpx.Response(200, json={"id": archived[-1], "archived": True})
        return httpx.Response(404, json={"message": "not found"})

    cfg = NotionConfig(database_id="db-test")
    with _patch_notion_http(handler):
        result = cleanup_board(token="tok", config=cfg)
    assert result.processed == 1
    assert archived == ["page-1"]


def test_import_tasks_deploys_enabled_pair(tmp_path: Path, monkeypatch) -> None:
    task_root = tmp_path / "tasks"
    for rel in ("header/sample.yaml", "body/sample.md"):
        src = FIXTURE_ROOT / rel
        dest = task_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    manifest = task_root / "tasks.pairs.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "header_filepath": "header/sample.yaml",
                    "body_filepath": "body/sample.md",
                }
            ]
        ),
        encoding="utf-8",
    )

    created: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path.endswith("/query"):
            return httpx.Response(200, json={"results": [], "has_more": False})
        if request.method == "POST" and request.url.path.endswith("/pages"):
            created.append(json.loads(request.content))
            return httpx.Response(200, json={"id": "new-page"})
        return httpx.Response(404, json={"message": "not found"})

    cfg = NotionConfig(database_id="db-test", cleanup_before_deploy=True)
    monkeypatch.setattr(
        "gardusig_cli.services.notion_sync.notion_pairs_file",
        lambda config_dir=None: manifest,
    )
    monkeypatch.setattr(
        "gardusig_cli.services.notion_sync.notion_task_root",
        lambda config_dir=None: task_root,
    )

    with _patch_notion_http(handler):
        result = import_tasks(task_root, token="tok", config=cfg, cleanup_first=True)

    assert result.processed == 1
    assert created
    props = created[0]["properties"]
    assert props["Name"]["title"][0]["text"]["content"] == "🧪 sample task"


def test_export_tasks_ingest_updates_local(tmp_path: Path, monkeypatch) -> None:
    task_root = tmp_path / "tasks"
    for rel in ("header/sample.yaml", "body/sample.md"):
        src = FIXTURE_ROOT / rel
        dest = task_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    manifest = task_root / "tasks.pairs.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "header_filepath": "header/sample.yaml",
                    "body_filepath": "body/sample.md",
                }
            ]
        ),
        encoding="utf-8",
    )

    page = {
        "id": "page-1",
        "archived": False,
        "properties": {
            "Name": {"title": [{"plain_text": "🧪 sample task", "type": "text"}]},
            "Priority": {"select": {"name": "2"}},
            "Tag": {"select": {"name": "ops"}},
            "Frequency": {"select": None},
            "Interval": {"number": None},
            "Last done": {"date": {"start": "2026-02-01"}},
            "Forced status": {"select": None},
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path.endswith("/query"):
            return httpx.Response(200, json={"results": [page], "has_more": False})
        if request.method == "GET" and "/children" in request.url.path:
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"plain_text": "Updated body", "type": "text"}]
                            },
                        }
                    ],
                    "has_more": False,
                },
            )
        return httpx.Response(404, json={"message": "not found"})

    cfg = NotionConfig(database_id="db-test")
    monkeypatch.setattr(
        "gardusig_cli.services.notion_sync.notion_pairs_file",
        lambda config_dir=None: manifest,
    )

    with _patch_notion_http(handler):
        result = export_tasks(task_root, token="tok", config=cfg)

    assert result.processed == 1
    meta_text = (task_root / "header/sample.yaml").read_text(encoding="utf-8")
    assert "last_done: '2026-02-01'" in meta_text or 'last_done: "2026-02-01"' in meta_text
    body_text = (task_root / "body/sample.md").read_text(encoding="utf-8")
    assert "Updated body" in body_text


def test_notion_client_page_title() -> None:
    cfg = NotionConfig(database_id="db")
    client = NotionClient("tok", config=cfg)
    title = client.page_title(
        {"properties": {"Name": {"title": [{"plain_text": "Hello", "type": "text"}]}}}
    )
    client.close()
    assert title == "Hello"
