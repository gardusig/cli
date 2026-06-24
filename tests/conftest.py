"""Shared pytest fixtures and hooks."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.constants import ROOT

from gardusig_cli.integration.docker_guard import in_docker_integration

DEFAULT_TEST_TIMEOUT_SECONDS = 30
INTEGRATION_TEST_TIMEOUT_SECONDS = 300



_DESELECTED: list[pytest.Item] = []


@pytest.fixture
def simulate_host_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pretend tests run on the host (no Docker harness env)."""
    monkeypatch.delenv("CLI_DOCKER_INTEGRATION", raising=False)
    monkeypatch.delenv("CLI_INTEGRATION_SCRATCH", raising=False)


@pytest.fixture(autouse=True)
def ci_config_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Use config/ci in Docker so tests never touch dev iCloud paths."""
    if in_docker_integration():
        monkeypatch.setenv("CLI_CONFIG_DIR", str(ROOT / "config" / "ci"))


def pytest_deselected(items: list[pytest.Item]) -> None:
    _DESELECTED.extend(items)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Integration tests need Docker; drop them on host pytest runs."""
    if not in_docker_integration():
        kept: list[pytest.Item] = []
        for item in items:
            if item.get_closest_marker("integration"):
                continue
            kept.append(item)
        items[:] = kept
    for item in items:
        if item.get_closest_marker("integration"):
            item.add_marker(pytest.mark.timeout(INTEGRATION_TEST_TIMEOUT_SECONDS))


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if not _DESELECTED:
        return
    if all(item.get_closest_marker("integration") for item in _DESELECTED):
        return
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
