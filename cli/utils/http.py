"""Shared HTTP client defaults."""

from __future__ import annotations

DEFAULT_HTTP_TIMEOUT_SECONDS = 30.0


def default_http_timeout() -> float:
    """Return the global HTTP request timeout in seconds."""
    return DEFAULT_HTTP_TIMEOUT_SECONDS
