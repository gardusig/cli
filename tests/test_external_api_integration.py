"""External API client: happy-path execution vs permanent/transient failures."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from gardusig_cli.cli import app, run
from gardusig_cli.integration.workspaces import API_WORKSPACES, fixture_dir
from gardusig_cli.services.notion_sync import export_tasks, import_tasks
from gardusig_cli.utils.config import NotionConfig
from gardusig_cli.utils.external_client import ExternalCallError, ExternalClient
from gardusig_cli.utils.process import GhCommandError
from tests.drive_harness import DriveRemoteError, FailingDriveProvider, InMemoryDriveProvider
from tests.gh_harness import gh_auth_error, gh_transient_error, patch_run_gh
from tests.integration_harness import copy_fixture_workspace
from tests.notion_harness import (
    deploy_ok_handler,
    notion_error_handler,
    notion_flaky_handler,
    notion_page,
    patch_notion_http,
)

NOTION_WS = next(w for w in API_WORKSPACES if w.name == "notion")
DRIVE_WS = next(w for w in API_WORKSPACES if w.name == "drive")
GH_WS = next(w for w in API_WORKSPACES if w.name == "gh")
RUNNER = CliRunner()


@pytest.fixture
def notion_task_root(tmp_path: Path) -> Path:
    return copy_fixture_workspace(NOTION_WS, tmp_path, dest_name="external-notion")


@pytest.fixture
def notion_paths(monkeypatch, notion_task_root: Path):
    manifest = notion_task_root / "tasks.pairs.json"

    monkeypatch.setattr(
        "gardusig_cli.services.notion_sync.notion_pairs_file",
        lambda config_dir=None: manifest,
    )
    monkeypatch.setattr(
        "gardusig_cli.services.notion_sync.notion_task_root",
        lambda config_dir=None: notion_task_root,
    )
    return notion_task_root, manifest


@pytest.mark.integration
def test_notion_deploy_full_happy_path(notion_paths) -> None:
    task_root, _ = notion_paths
    cfg = NotionConfig(database_id="db-external", cleanup_before_deploy=False)
    created: list[dict] = []

    with patch_notion_http(deploy_ok_handler(created)):
        result = import_tasks(task_root, token="tok", config=cfg, cleanup_first=False)

    assert result.processed == 2
    assert len(created) == 2


@pytest.mark.integration
def test_notion_deploy_401_fails_with_user_hint(notion_paths) -> None:
    task_root, _ = notion_paths
    cfg = NotionConfig(database_id="db-external", cleanup_before_deploy=False)

    with patch_notion_http(notion_error_handler(401, message="invalid token")):
        with pytest.raises(ExternalCallError) as exc_info:
            import_tasks(task_root, token="bad", config=cfg, cleanup_first=False)

    message = exc_info.value.user_message
    assert "NOTION_TOKEN" in message
    assert "401" in message


@pytest.mark.integration
def test_notion_deploy_503_retries_then_succeeds(notion_paths) -> None:
    task_root, _ = notion_paths
    cfg = NotionConfig(database_id="db-external", cleanup_before_deploy=False)
    handler = notion_flaky_handler(
        deploy_ok_handler(),
        failures_before_ok=1,
        fail_status=503,
    )
    client = ExternalClient("notion", sleep=lambda _s: None)

    with patch_notion_http(handler):
        with patch("gardusig_cli.providers.notion.ExternalClient", return_value=client):
            result = import_tasks(task_root, token="tok", config=cfg, cleanup_first=False)

    assert result.processed == 2


@pytest.mark.integration
def test_notion_ingest_403_fails_without_retry(notion_paths) -> None:
    task_root, _ = notion_paths
    cfg = NotionConfig(database_id="db-external")

    with patch_notion_http(notion_error_handler(403, message="restricted")):
        with pytest.raises(ExternalCallError) as exc_info:
            export_tasks(task_root, token="tok", config=cfg)

    assert "permission" in exc_info.value.user_message.casefold()


@pytest.mark.integration
def test_gh_issue_list_happy_path_via_run_gh() -> None:
    fixture = fixture_dir(GH_WS) / "issues.json"
    issues = json.loads(fixture.read_text(encoding="utf-8"))

    def handler(args, *, cwd=None, check=True):
        if args[:2] == ["issue", "list"]:
            from subprocess import CompletedProcess

            return CompletedProcess(args, 0, json.dumps(issues), "")
        raise GhCommandError(args, 1, f"unmocked: {args}")

    with patch_run_gh(handler=handler):
        result = RUNNER.invoke(app, ["gh", "--format", "json", "issue", "list"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload[0]["number"] == 42


@pytest.mark.integration
def test_gh_issue_list_auth_failure_surfaces_hint() -> None:
    from gardusig_cli.providers.gh import GhProvider

    with patch_run_gh(side_effect=gh_auth_error()):
        with pytest.raises(ExternalCallError) as exc_info:
            GhProvider().run_json(
                [
                    "issue",
                    "list",
                    "--state",
                    "open",
                    "--limit",
                    "30",
                    "--json",
                    "number,title,state,labels,url",
                ]
            )

    assert "gh auth login" in exc_info.value.user_message.casefold()


@pytest.mark.integration
def test_gh_issue_list_transient_503_retries_then_succeeds() -> None:
    fixture = fixture_dir(GH_WS) / "issues.json"
    issues = json.loads(fixture.read_text(encoding="utf-8"))
    state = {"failures": 0}

    def handler(args, *, cwd=None, check=True):
        if args[:2] != ["issue", "list"]:
            raise GhCommandError(args, 1, f"unmocked: {args}")
        if state["failures"] < 1:
            state["failures"] += 1
            raise gh_transient_error()
        from subprocess import CompletedProcess

        return CompletedProcess(args, 0, json.dumps(issues), "")

    client = ExternalClient("gh", sleep=lambda _s: None)

    with patch_run_gh(handler=handler):
        with patch("gardusig_cli.providers.gh.ExternalClient", return_value=client):
            result = RUNNER.invoke(app, ["gh", "--format", "json", "issue", "list"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)[0]["number"] == 42


@pytest.mark.integration
def test_drive_upload_happy_path(tmp_path: Path) -> None:
    from gardusig_cli.services.drive_sync import upload_missing

    workspace = copy_fixture_workspace(DRIVE_WS, tmp_path)
    local_root = workspace / "tags"
    provider = InMemoryDriveProvider()

    result = upload_missing(local_root, provider, "backups/tags")

    assert result.failed == []
    assert "demo-repo/demo-repo-v1.0.0.zip" in result.uploaded


@pytest.mark.integration
def test_drive_upload_permanent_list_failure_stops_with_hint(tmp_path: Path) -> None:
    from gardusig_cli.services.drive_sync import upload_missing

    workspace = copy_fixture_workspace(DRIVE_WS, tmp_path)
    local_root = workspace / "tags"
    provider = FailingDriveProvider(
        operation="list_files",
        error=DriveRemoteError("credentials expired", retryable=False),
        failures_before_ok=10,
    )

    with pytest.raises(ExternalCallError) as exc_info:
        upload_missing(local_root, provider, "backups/tags")

    assert "drive" in exc_info.value.user_message.casefold()
    assert "credentials" in exc_info.value.user_message.casefold()


@pytest.mark.integration
def test_drive_upload_transient_list_retries_then_succeeds(tmp_path: Path) -> None:
    from gardusig_cli.services.drive_sync import upload_missing

    workspace = copy_fixture_workspace(DRIVE_WS, tmp_path)
    local_root = workspace / "tags"
    provider = FailingDriveProvider(
        operation="list_files",
        error=DriveRemoteError("503 upstream", retryable=True),
        failures_before_ok=1,
    )
    client = ExternalClient("drive", sleep=lambda _s: None)

    with patch("gardusig_cli.providers.drive_client.ExternalClient", return_value=client):
        result = upload_missing(local_root, provider, "backups/tags")

    assert result.failed == []
    assert "demo-repo/demo-repo-v1.0.0.zip" in result.uploaded


@pytest.mark.integration
def test_cli_run_entrypoint_maps_external_call_error(capsys, monkeypatch) -> None:
    import sys
    import typer

    monkeypatch.setattr(
        sys,
        "argv",
        ["cli", "gh", "--format", "json", "issue", "list"],
    )

    with patch_run_gh(side_effect=gh_auth_error()):
        with pytest.raises(typer.Exit) as exc_info:
            run()

    assert exc_info.value.exit_code == 1
    captured = capsys.readouterr()
    assert "gh auth login" in (captured.err + captured.out).casefold()
