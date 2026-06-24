"""Unit tests for ExternalClient retry and user-facing errors."""

from __future__ import annotations

from tests.constants import ROOT

import httpx
import pytest

from gardusig_cli.providers.notion import NotionError
from gardusig_cli.utils.external_client import (
    ExternalCallError,
    ExternalClient,
    failure_hint,
    format_user_message,
    is_retryable_exception,
)
from gardusig_cli.utils.process import GhCommandError


def test_is_retryable_notion_503() -> None:
    assert is_retryable_exception(NotionError("down", status_code=503)) is True


def test_is_retryable_notion_401_not_retried() -> None:
    assert is_retryable_exception(NotionError("bad token", status_code=401)) is False


def test_is_retryable_gh_transient_stderr() -> None:
    exc = GhCommandError(["gh", "pr", "list"], 1, "HTTP 503 service unavailable")
    assert is_retryable_exception(exc) is True


def test_is_retryable_gh_auth_not_retried() -> None:
    exc = GhCommandError(["gh", "issue", "list"], 1, "not logged in")
    assert is_retryable_exception(exc) is False


def test_is_retryable_retryable_attribute() -> None:
    class Transient(RuntimeError):
        retryable = True

    assert is_retryable_exception(Transient("x")) is True


def test_external_client_retries_then_raises_user_message() -> None:
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        raise NotionError("down", status_code=503)

    client = ExternalClient("notion", attempts=3, sleep=lambda _s: None)

    with pytest.raises(ExternalCallError) as exc_info:
        client.call("query database", flaky)

    assert calls["n"] == 3
    assert "notion query database failed" in exc_info.value.user_message
    assert "server error" in exc_info.value.user_message.casefold()


def test_external_client_succeeds_after_transient_failure() -> None:
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 2:
            raise httpx.ConnectError("connection reset")
        return "ok"

    client = ExternalClient("notion", attempts=3, sleep=lambda _s: None)
    assert client.call("GET /pages", flaky) == "ok"
    assert calls["n"] == 2


def test_failure_hint_notion_401() -> None:
    hint = failure_hint("notion", "query", NotionError("x", status_code=401))
    assert "NOTION_TOKEN" in hint


def test_format_user_message_includes_attempt_count() -> None:
    msg = format_user_message(
        "gh",
        "issue list",
        GhCommandError(["gh"], 1, "fail"),
        attempts=3,
    )
    assert "3 attempt" in msg
    assert "What to try:" in msg
