"""Integration tests for git tag and zip workflows."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from shuttle.integration.tag_zip_integration import (
    TAG_ZIP_CHECKS,
    prepare_tag_zip_git,
    run_all_tag_zip_checks,
)

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / ".integration-scratch"


@pytest.fixture
def git_repo():
    SCRATCH.mkdir(exist_ok=True)
    git_dir = Path(tempfile.mkdtemp(prefix="shuttle-tag-zip-", dir=SCRATCH))
    bare = git_dir.parent / f"{git_dir.name}-origin.git"
    prepare_tag_zip_git(git_dir)
    try:
        yield git_dir
    finally:
        shutil.rmtree(git_dir, ignore_errors=True)
        shutil.rmtree(bare, ignore_errors=True)


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
