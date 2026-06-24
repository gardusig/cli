"""Shared pytest fixtures and hooks."""

from __future__ import annotations

import pytest

DEFAULT_TEST_TIMEOUT_SECONDS = 30
INTEGRATION_TEST_TIMEOUT_SECONDS = 300

_DESELECTED: list[pytest.Item] = []


def pytest_deselected(items: list[pytest.Item]) -> None:
    _DESELECTED.extend(items)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Integration tests may build images or run Docker — allow more time."""
    for item in items:
        if item.get_closest_marker("integration"):
            item.add_marker(pytest.mark.timeout(INTEGRATION_TEST_TIMEOUT_SECONDS))


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if _DESELECTED:
        sample = ", ".join(item.nodeid for item in _DESELECTED[:5])
        extra = f" (+{len(_DESELECTED) - 5} more)" if len(_DESELECTED) > 5 else ""
        pytest.fail(
            f"Deselected tests are not allowed ({len(_DESELECTED)}): {sample}{extra}"
        )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> None:
    """Treat any skipped test as a failure — the suite must run completely."""
    outcome = yield
    report = outcome.get_result()
    if report.skipped:
        reason = getattr(report.longrepr, "reprcrash", None)
        detail = str(reason.message) if reason is not None else str(report.longrepr)
        pytest.fail(f"Skipped tests are not allowed ({item.nodeid}): {detail}")
