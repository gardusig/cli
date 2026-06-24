"""Integration tests for git tag and zip workflows."""

from __future__ import annotations

from pathlib import Path

import pytest

from gardusig_cli.integration.docker_guard import cleanup_integration_temp_dir, integration_temp_dir
from gardusig_cli.integration.tag_zip_integration import (
    TAG_ZIP_CHECKS,
    prepare_tag_zip_git,
    run_all_tag_zip_checks,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def git_repo():
    git_dir = integration_temp_dir("cli-tag-zip-")
    prepare_tag_zip_git(git_dir)
    try:
        yield git_dir
    finally:
        cleanup_integration_temp_dir(git_dir)


@pytest.mark.integration
@pytest.mark.parametrize(
    ("check_fn",),
    [(fn,) for _, fn in TAG_ZIP_CHECKS],
    ids=[label for label, _ in TAG_ZIP_CHECKS],
)
def test_tag_zip_scenario(git_repo: Path, check_fn) -> None:
    errors = check_fn(git_repo, ROOT)
    assert errors == [], "\n".join(errors)


@pytest.mark.integration
def test_run_all_tag_zip_checks(git_repo: Path) -> None:
    errors = run_all_tag_zip_checks(ROOT, git_repo)
    assert errors == [], "\n---\n".join(errors)
