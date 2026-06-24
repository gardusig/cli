"""Drive upload_missing against an in-memory provider (isolated local tags)."""

from __future__ import annotations

from tests.constants import ROOT

from pathlib import Path

import pytest

from src.integration.workspaces import API_WORKSPACES
from src.services.drive_sync import upload_missing
from tests.harness.drive_harness import InMemoryDriveProvider
from tests.harness.integration_harness import copy_fixture_workspace, protected_repo_guard

DRIVE_WS = next(w for w in API_WORKSPACES if w.name == "drive")


@pytest.mark.integration
def test_upload_missing_pushes_local_tags_to_mock_remote(tmp_path: Path) -> None:
    workspace = copy_fixture_workspace(DRIVE_WS, tmp_path)
    local_root = workspace / "tags"
    provider = InMemoryDriveProvider()
    remote_root = "backups/tags"

    with protected_repo_guard(DRIVE_WS):
        result = upload_missing(local_root, provider, remote_root)

    assert result.failed == []
    assert "demo-repo/demo-repo-v1.0.0.zip" in result.uploaded
    assert provider.exists(f"{remote_root}/demo-repo/demo-repo-v1.0.0.zip")


@pytest.mark.integration
def test_upload_missing_skips_existing_remote_files(tmp_path: Path) -> None:
    workspace = copy_fixture_workspace(DRIVE_WS, tmp_path)
    local_root = workspace / "tags"
    provider = InMemoryDriveProvider()
    remote_root = "backups/tags"

    first = upload_missing(local_root, provider, remote_root)
    second = upload_missing(local_root, provider, remote_root)

    assert first.failed == []
    assert "demo-repo/demo-repo-v1.0.0.zip" in first.uploaded
    assert second.skipped == ["demo-repo/demo-repo-v1.0.0.zip"]
    assert second.uploaded == []
