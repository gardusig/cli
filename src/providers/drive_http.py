"""Shared HTTP helpers for cloud drive providers."""

from __future__ import annotations

from pathlib import Path

import httpx

from src.utils.http import default_http_timeout


class DriveApiError(RuntimeError):
    """Drive API failure with optional HTTP status and retry hint."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


def split_remote_path(path: str) -> tuple[str, str]:
    """Split ``parent/child`` remote path into parent prefix and final segment."""
    cleaned = path.strip("/").replace("\\", "/")
    if not cleaned:
        return "", ""
    if "/" not in cleaned:
        return "", cleaned
    parent, name = cleaned.rsplit("/", 1)
    return parent, name


def join_remote_path(root: str, relative: str) -> str:
    root = root.strip("/")
    relative = relative.strip("/")
    if root and relative:
        return f"{root}/{relative}"
    return root or relative


def bearer_client(token: str, *, base_url: str) -> httpx.Client:
    return httpx.Client(
        base_url=base_url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=default_http_timeout(),
    )


def raise_for_status(response: httpx.Response, *, operation: str) -> None:
    if response.is_success:
        return
    status = response.status_code
    retryable = status in {408, 429, 500, 502, 503, 504}
    detail = response.text.strip() or response.reason_phrase
    raise DriveApiError(
        f"{operation} failed (HTTP {status}): {detail}",
        status_code=status,
        retryable=retryable,
    )


def read_local_bytes(path: Path) -> bytes:
    return path.read_bytes()
