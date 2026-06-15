"""Shared pytest fixtures and hooks."""

from __future__ import annotations

import pytest


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> None:
    """Treat any skipped test as a failure — the suite must run completely."""
    outcome = yield
    report = outcome.get_result()
    if report.skipped:
        reason = getattr(report.longrepr, "reprcrash", None)
        detail = str(reason.message) if reason is not None else str(report.longrepr)
        pytest.fail(f"Skipped tests are not allowed ({item.nodeid}): {detail}")
