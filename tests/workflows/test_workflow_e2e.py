"""Parametrized end-to-end workflow integration tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

from tests.constants import ROOT

import pytest

from src.integration.docker_guard import (
    cleanup_integration_temp_dir,
    integration_scratch_dir,
)
from src.integration.public_endpoints import prepare_git_repo
from src.integration.workflows import WORKFLOW_REGISTRY

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("label,check_fn", WORKFLOW_REGISTRY)
def test_workflow_e2e(label: str, check_fn) -> None:
    scratch = integration_scratch_dir(require_docker=False)
    git_dir = Path(tempfile.mkdtemp(prefix="cli-workflow-e2e-", dir=scratch))
    try:
        prepare_git_repo(git_dir)
        errors = check_fn(git_dir, ROOT)
        assert not errors, f"workflow {label!r} failed:\n" + "\n".join(errors)
    finally:
        cleanup_integration_temp_dir(git_dir)
