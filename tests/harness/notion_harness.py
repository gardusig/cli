"""Shared Notion HTTP mocks for integration tests."""

from __future__ import annotations

from tests.constants import ROOT

import json
from typing import Any

import httpx

from gardusig_cli.utils.http import default_http_timeout

NOTION_BASE = "https://api.notion.com/v1"
_REAL_HTTPX_CLIENT = httpx.Client


def patch_notion_http(handler):
    def _client_factory(**kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        kwargs.setdefault("base_url", NOTION_BASE)
        kwargs.setdefault("timeout", default_http_timeout())
        return _REAL_HTTPX_CLIENT(**kwargs)

    from unittest.mock import patch

    return patch(
        "gardusig_cli.providers.notion.httpx.Client",
        side_effect=_client_factory,
    )


def notion_page(
    *,
    page_id: str,
    title: str,
    priority: str = "2",
    body_blocks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": page_id,
        "archived": False,
        "properties": {
            "Name": {"title": [{"plain_text": title, "type": "text"}]},
            "Priority": {"select": {"name": priority}},
            "Tag": {"select": {"name": "ops"}},
            "Frequency": {"select": {"name": "weeks"}},
            "Interval": {"number": 1},
            "Last done": {"date": {"start": "2026-03-01"}},
            "Forced status": {"select": None},
        },
        "_body_blocks": body_blocks
        or [
            {
                "type": "heading_2",
                "heading_2": {"rich_text": [{"plain_text": "Steps", "type": "text"}]},
            },
            {
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"plain_text": "From Notion", "type": "text"}],
                    "checked": False,
                },
            },
        ],
    }


def deploy_ok_handler(created: list[dict[str, Any]] | None = None):
    """Mock Notion API: archive query returns empty; page create returns 200."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path.endswith("/query"):
            return httpx.Response(200, json={"results": [], "has_more": False})
        if request.method == "POST" and request.url.path.endswith("/pages"):
            payload = json.loads(request.content)
            if created is not None:
                created.append(payload)
            return httpx.Response(200, json={"id": "new-page"})
        return httpx.Response(200, json={"id": "ok"})

    return handler


def ingest_handler(pages: list[dict[str, Any]]):
    """Mock Notion API: database query returns pages; children per page id."""

    bodies = {p["id"]: p.pop("_body_blocks", []) for p in pages}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path.endswith("/query"):
            return httpx.Response(
                200,
                json={"results": pages, "has_more": False},
            )
        if request.method == "GET" and "/children" in request.url.path:
            page_id = request.url.path.split("/")[3]
            return httpx.Response(
                200,
                json={"results": bodies.get(page_id, []), "has_more": False},
            )
        return httpx.Response(200, json={"id": "ok"})

    return handler


def notion_cli_handler(pages: list[dict[str, Any]] | None = None):
    """Mock Notion API for full CLI ingest + deploy cycle."""

    source = pages or [notion_page(page_id="p1", title="✅ complete task")]
    ingest_pages = [dict(p) for p in source]
    ingest = ingest_handler(ingest_pages)
    deploy = deploy_ok_handler()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path.endswith("/pages"):
            return deploy(request)
        return ingest(request)

    return handler


def notion_error_handler(status: int, *, message: str | None = None):
    """Always return a fixed HTTP status (for permanent failure tests)."""

    body = {"message": message or f"HTTP {status}"}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json=body)

    return handler


def notion_flaky_handler(
    inner,
    *,
    fail_status: int = 503,
    failures_before_ok: int = 1,
    message: str = "Service unavailable",
):
    """Fail the first N requests, then delegate to inner handler."""

    state = {"failures": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if state["failures"] < failures_before_ok:
            state["failures"] += 1
            return httpx.Response(fail_status, json={"message": message})
        return inner(request)

    return handler
