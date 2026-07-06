"""Retrying wrapper for external API / CLI calls with user-facing errors."""

from __future__ import annotations

import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

import httpx

from src.utils.process import GhCommandError

T = TypeVar("T")

_RETRYABLE_HTTP = frozenset({408, 429, 500, 502, 503, 504})


@dataclass
class ExternalCallError(RuntimeError):
    """External dependency failed after retries — safe to show the user."""

    service: str
    operation: str
    user_message: str
    cause: Exception | None = None
    status_code: int | None = None
    attempts: int = 0

    def __str__(self) -> str:
        return self.user_message


def is_retryable_http_status(status_code: int | None) -> bool:
    return status_code in _RETRYABLE_HTTP if status_code is not None else False


def is_retryable_exception(exc: Exception) -> bool:
    if getattr(exc, "retryable", False) is True:
        return True
    if isinstance(exc, httpx.TimeoutException | httpx.NetworkError | httpx.TransportError):
        return True
    if isinstance(exc, subprocess.TimeoutExpired):
        return True
    status_code = getattr(exc, "status_code", None)
    if exc.__class__.__name__ == "NotionError" and isinstance(status_code, int):
        return is_retryable_http_status(status_code)
    if isinstance(exc, GhCommandError):
        text = exc.stderr.casefold()
        return any(
            token in text
            for token in ("rate limit", "timed out", "timeout", "502", "503", "504")
        )
    if exc.__class__.__name__ == "DriveApiError" and getattr(exc, "retryable", False):
        return True
    return False


def failure_hint(service: str, operation: str, exc: Exception) -> str:
    if exc.__class__.__name__ == "NotionError":
        status = getattr(exc, "status_code", None)
        hints = {
            401: "Check NOTION_TOKEN is valid and the integration is still active.",
            403: "The token lacks permission for this database or page.",
            404: "The database or page was not found — verify notion.database_id and board access.",
            429: "Notion rate-limited the request; wait a moment and try again.",
        }
        if status in hints:
            return hints[status]
        if status and status >= 500:
            return "Notion returned a server error; retry later."
        return "Verify the Notion integration, database id, and network connectivity."
    if isinstance(exc, GhCommandError):
        if "not logged" in exc.stderr.casefold() or "auth" in exc.stderr.casefold():
            return "Run `gh auth login` and confirm `gh auth status`."
        if exc.returncode == 127:
            return "Install GitHub CLI (`gh`) and ensure it is on PATH."
        return "Check `gh auth status`, repository access, and network connectivity."
    if service == "drive":
        return "Check drive provider credentials, remote root path, and network connectivity."
    return f"Verify {service} configuration and network connectivity."


def format_user_message(
    service: str,
    operation: str,
    exc: Exception,
    *,
    attempts: int,
) -> str:
    hint = failure_hint(service, operation, exc)
    status = getattr(exc, "status_code", None)
    status_part = f" (HTTP {status})" if status else ""
    return (
        f"{service} {operation} failed after {attempts} attempt(s){status_part}.\n"
        f"Reason: {exc}\n"
        f"What to try: {hint}"
    )


class ExternalClient:
    """Execute external calls with exponential backoff and a single user-facing error."""

    def __init__(
        self,
        service: str,
        *,
        attempts: int = 3,
        base_delay: float = 0.5,
        max_delay: float = 8.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.service = service
        self.attempts = max(1, attempts)
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._sleep = sleep

    def call(self, operation: str, fn: Callable[[], T]) -> T:
        last: Exception | None = None
        for attempt in range(1, self.attempts + 1):
            try:
                return fn()
            except Exception as exc:
                last = exc
                if attempt >= self.attempts or not is_retryable_exception(exc):
                    break
                delay = min(self.base_delay * (2 ** (attempt - 1)), self.max_delay)
                self._sleep(delay)
        assert last is not None
        status_code = getattr(last, "status_code", None)
        raise ExternalCallError(
            service=self.service,
            operation=operation,
            user_message=format_user_message(
                self.service,
                operation,
                last,
                attempts=self.attempts,
            ),
            cause=last,
            status_code=status_code,
            attempts=self.attempts,
        ) from last
