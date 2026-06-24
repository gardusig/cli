"""Retry helpers — delegates to ExternalClient."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from gardusig_cli.utils.external_client import ExternalClient

T = TypeVar("T")


def retry(
    fn: Callable[[], T],
    *,
    attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    service: str = "external",
    operation: str = "call",
) -> T:
    """Run fn with exponential backoff; raises ExternalCallError when exhausted."""

    client = ExternalClient(
        service,
        attempts=attempts,
        base_delay=delay,
        max_delay=delay * (2 ** max(0, attempts - 1)),
    )
    return client.call(operation, fn)
