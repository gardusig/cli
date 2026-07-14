"""Shared pytest fixtures and hooks."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from tests.constants import ROOT, TEST_CONFIG_DIR

from src.integration.docker_guard import in_docker_integration

DEFAULT_TEST_TIMEOUT_SECONDS = 30
INTEGRATION_TEST_TIMEOUT_SECONDS = 300


_DESELECTED: list[pytest.Item] = []


@pytest.fixture(scope="session", autouse=True)
def docker_unit_git_root() -> None:
    """Docker unit images omit .git; bootstrap a synthetic repo at the workspace root."""
    if (ROOT / ".git").is_dir():
        return
    if in_docker_integration():
        return
    # Only bootstrap in CI Docker unit images (/workspace, no .git in COPY context).
    if os.environ.get("GITHUB_ACTIONS") != "true" and str(ROOT) != "/workspace":
        return

    subprocess.run(["git", "init", "-b", "main"], cwd=ROOT, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "unit@test"], cwd=ROOT, check=True)
    subprocess.run(["git", "config", "user.name", "unit"], cwd=ROOT, check=True)
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(
        ["git", "commit", "-m", "ci-init", "--allow-empty"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    os.environ["CLI_UNIT_GIT_BOOTSTRAP"] = "1"


@pytest.fixture
def simulate_host_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pretend tests run on the host (no Docker harness env)."""
    monkeypatch.delenv("CLI_DOCKER_INTEGRATION", raising=False)
    monkeypatch.delenv("CLI_INTEGRATION_SCRATCH", raising=False)


@pytest.fixture(scope="session", autouse=True)
def _load_local_env() -> None:
    from src.utils.config import load_local_env

    load_local_env()


@pytest.fixture(autouse=True)
def test_config_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    """Repo config + test profile overlay (never the developer home dir)."""

    def _test_default_config_dir() -> Path:
        env = os.environ.get("CLI_CONFIG_DIR", "").strip()
        if env:
            return Path(env).expanduser()
        return TEST_CONFIG_DIR

    monkeypatch.delenv("CLI_CONFIG_DIR", raising=False)
    monkeypatch.setenv("CLI_PROFILE", "test")
    monkeypatch.setattr("src.utils.config.default_config_dir", _test_default_config_dir)


def _docs_available() -> bool:
    return (ROOT / "docs" / "release.md").is_file()


def _contest_runner_image_ready() -> bool:
    try:
        from src.services.docker_runtime import ensure_docker, run_docker

        ensure_docker()
    except RuntimeError:
        return False
    return run_docker(["image", "inspect", "cli-contest:runner"], check=False).returncode == 0


def _github_pipelines_python_cli_config() -> bool:
    config = (
        ROOT.parent
        / "github-pipelines"
        / ".github"
        / "workflows"
        / "pull-request"
        / "python-cli.yaml"
    )
    return config.is_file()


def _local_pull_request_workflow_configs() -> bool:
    github_roots = [ROOT.parent, ROOT.parent.parent / "private"]
    for github_root in github_roots:
        if not github_root.is_dir():
            continue
        for repo_root in github_root.iterdir():
            if not repo_root.is_dir():
                continue
            for config_name in ("pull-request.yaml",):
                config = repo_root / ".github" / "workflows" / config_name
                if not config.is_file():
                    config = repo_root / ".github" / config_name
                if config.is_file():
                    return True
    return False


def _optional_integration_ready(item: pytest.Item) -> bool:
    """Drop env-specific integration tests at collection time (skips are forbidden)."""
    checks: dict[str, bool] = {
        "test_contest_validate_toy_live": _contest_runner_image_ready(),
        "test_python_cli_pipeline_config_resolve_against_pipelines": _github_pipelines_python_cli_config(),
        "test_pull_request_configs_declare_inline_hygiene_policies": _local_pull_request_workflow_configs(),
    }
    ready = checks.get(item.name)
    if ready is None:
        return True
    return ready


def pytest_deselected(items: list[pytest.Item]) -> None:
    _DESELECTED.extend(items)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Integration tests need Docker; drop them on host pytest runs."""
    docs_available = _docs_available()
    kept: list[pytest.Item] = []
    for item in items:
        if item.get_closest_marker("requires_docs") and not docs_available:
            if not item.get_closest_marker("integration"):
                item.add_marker(pytest.mark.integration)
            continue
        if not in_docker_integration() and item.get_closest_marker("integration"):
            continue
        if item.get_closest_marker("integration") and not _optional_integration_ready(item):
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
    # Marker filters (e.g. -m integration) legitimately deselect the complementary suite.
    if session.config.getoption("markexpr", default=""):
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
