"""Notion API client (httpx)."""

from __future__ import annotations

from typing import Any

import httpx

from src.services.notion_markdown import blocks_to_task_body, markdown_to_blocks, strip_leading_title_heading
from src.utils.config import NotionConfig, NotionPropertyMap
from src.utils.external_client import ExternalClient
from src.utils.http import default_http_timeout

NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"


class NotionError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class NotionClient:
    def __init__(self, token: str, *, config: NotionConfig) -> None:
        self._config = config
        self._props = config.properties
        self._external = ExternalClient("notion")
        self._http = httpx.Client(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            },
            timeout=default_http_timeout(),
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> NotionClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def query_database_pages(self, database_id: str) -> list[dict[str, Any]]:
        pages: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            body: dict[str, Any] = {}
            if cursor:
                body["start_cursor"] = cursor
            data = self._post(f"/databases/{database_id}/query", body)
            pages.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        return pages

    def archive_page(self, page_id: str) -> None:
        self._patch(f"/pages/{page_id}", {"archived": True})

    def archive_all_in_database(self, database_id: str) -> int:
        count = 0
        for page in self.query_database_pages(database_id):
            if page.get("archived"):
                continue
            self.archive_page(page["id"])
            count += 1
        return count

    def get_page_blocks(self, page_id: str) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            params: dict[str, str] = {}
            if cursor:
                params["start_cursor"] = cursor
            data = self._get(f"/blocks/{page_id}/children", params=params)
            blocks.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        return blocks

    def create_database_page(
        self,
        database_id: str,
        *,
        title: str,
        metadata: dict[str, Any],
        body_markdown: str,
    ) -> dict[str, Any]:
        properties = self._metadata_to_properties(title, metadata)
        children = markdown_to_blocks(body_markdown)
        payload: dict[str, Any] = {
            "parent": {"database_id": database_id},
            "properties": properties,
        }
        if children:
            payload["children"] = children
        return self._post("/pages", payload)

    def page_title(self, page: dict[str, Any]) -> str:
        prop = page.get("properties", {}).get(self._props.title, {})
        return _plain_rich_text(prop.get("title", []))

    def page_metadata(self, page: dict[str, Any]) -> dict[str, Any]:
        props = page.get("properties", {})
        return {
            "priority": _read_number_or_select(props, self._props.priority),
            "tag": _read_select(props, self._props.tag),
            "frequency": _read_select(props, self._props.frequency),
            "interval": _read_number(props, self._props.interval),
            "last_done": _read_date(props, self._props.last_done),
            "forced_status": _read_select(props, self._props.forced_status),
            "link": _read_url(props, self._props.link),
        }

    def page_body_markdown(self, page_id: str, *, task_name: str = "") -> str:
        blocks = self.get_page_blocks(page_id)
        content = [b for b in blocks if not b.get("archived")]
        return blocks_to_task_body(content, task_name=task_name)

    def _metadata_to_properties(
        self, title: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        p = self._props
        out: dict[str, Any] = {
            p.title: {"title": [_text_chunk(title)]},
        }
        if metadata.get("priority") is not None:
            out[p.priority] = {
                "select": {"name": str(metadata["priority"])}
            }
        if metadata.get("tag"):
            out[p.tag] = {"select": {"name": str(metadata["tag"])}}
        if metadata.get("frequency"):
            out[p.frequency] = {"select": {"name": str(metadata["frequency"])}}
        if metadata.get("interval") is not None:
            out[p.interval] = {"number": int(metadata["interval"])}
        if metadata.get("last_done"):
            out[p.last_done] = {"date": {"start": str(metadata["last_done"])}}
        if metadata.get("forced_status"):
            out[p.forced_status] = {
                "select": {"name": str(metadata["forced_status"])}
            }
        if metadata.get("link"):
            out[p.link] = {"url": str(metadata["link"])}
        return out

    def _get(self, path: str, *, params: dict[str, str] | None = None) -> dict[str, Any]:
        return self._external.call(
            f"GET {path}",
            lambda: self._json(self._http.get(path, params=params)),
        )

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        return self._external.call(
            f"POST {path}",
            lambda: self._json(self._http.post(path, json=body)),
        )

    def _patch(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        return self._external.call(
            f"PATCH {path}",
            lambda: self._json(self._http.patch(path, json=body)),
        )

    def _json(self, resp: httpx.Response) -> dict[str, Any]:
        if resp.is_success:
            return resp.json()
        detail = resp.text
        try:
            detail = resp.json().get("message", detail)
        except Exception:
            pass
        raise NotionError(
            f"Notion API {resp.request.method} {resp.request.url}: {detail}",
            status_code=resp.status_code,
        )


def _text_chunk(text: str) -> dict[str, Any]:
    return {"type": "text", "text": {"content": text}}


def _plain_rich_text(rich_text: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for part in rich_text:
        if part.get("plain_text"):
            parts.append(part["plain_text"])
        elif part.get("type") == "text":
            parts.append(part.get("text", {}).get("content", ""))
    return "".join(parts)


def _read_select(props: dict[str, Any], name: str) -> str | None:
    prop = props.get(name, {})
    select = prop.get("select")
    if not select:
        return None
    return select.get("name")


def _read_number(props: dict[str, Any], name: str) -> int | None:
    prop = props.get(name, {})
    value = prop.get("number")
    if value is None:
        return None
    return int(value)


def _read_number_or_select(props: dict[str, Any], name: str) -> int | None:
    prop = props.get(name, {})
    if "number" in prop and prop["number"] is not None:
        return int(prop["number"])
    select = prop.get("select")
    if select and select.get("name") is not None:
        try:
            return int(select["name"])
        except ValueError:
            return None
    return None


def _read_date(props: dict[str, Any], name: str) -> str | None:
    prop = props.get(name, {})
    date = prop.get("date")
    if not date:
        return None
    return date.get("start")


def _read_url(props: dict[str, Any], name: str) -> str | None:
    prop = props.get(name, {})
    url = prop.get("url")
    if not url:
        return None
    return str(url)


# Deprecated provider-level stubs (use NotionClient via notion_sync).
def export_tasks(_database_id: str, _dest: str) -> None:
    raise NotImplementedError(
        "Use cli.services.notion_sync.export_tasks via cli notion ingest"
    )


def import_tasks(_database_id: str, _src: str) -> None:
    raise NotImplementedError(
        "Use cli.services.notion_sync.import_tasks via cli notion deploy"
    )
