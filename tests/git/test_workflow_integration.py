"""Integration tests for common start / push / reset workflows."""

from __future__ import annotations

from tests.constants import ROOT

from pathlib import Path

import pytest

from gardusig_cli.integration.docker_guard import cleanup_integration_temp_dir, integration_temp_dir
from gardusig_cli.integration.workflow_integration import (
    WORKFLOW_CHECKS,
    prepare_workflow_git,
    run_all_workflow_checks,
)


@pytest.fixture
def git_repo():
    git_dir = integration_temp_dir("cli-workflow-")
    prepare_workflow_git(git_dir)
    try:
        yield git_dir
    finally:
        cleanup_integration_temp_dir(git_dir)


@pytest.mark.integration
@pytest.mark.parametrize(
    ("check_fn",),
    [(fn,) for _, fn in WORKFLOW_CHECKS],
    ids=[label for label, _ in WORKFLOW_CHECKS],
)
def test_workflow_scenario(git_repo: Path, check_fn) -> None:
    errors = check_fn(git_repo, ROOT)
    assert errors == [], "\n".join(errors)


@pytest.mark.integration
def test_run_all_workflow_checks(git_repo: Path) -> None:
    errors = run_all_workflow_checks(ROOT, git_repo)
    assert errors == [], "\n---\n".join(errors)
