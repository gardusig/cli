"""Shared setup for mocked CLI API integration tests."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from cli.integration.cli_api_checks import CliApiCheck, validate_cli_api_check
from cli.integration.workspaces import API_WORKSPACES, fixture_dir
from cli.services.backup_repository import RepoBackupStatus, SyncResult
from cli.services.drive_sync import DriveSyncResult, UploadResult
from tests.drive_harness import InMemoryDriveProvider
from tests.gh_harness import gh_auth_error, patch_run_gh
from tests.integration_harness import copy_fixture_workspace
from tests.notion_harness import notion_cli_handler, notion_page, patch_notion_http

ROOT = Path(__file__).resolve().parents[1]
NOTION_WS = next(w for w in API_WORKSPACES if w.name == "notion")
NOTION_CLI_WS = ROOT / "tests" / "fixtures" / "notion" / "cli-workspace"
CHROME_WS = next(w for w in API_WORKSPACES if w.name == "chrome")
DRIVE_WS = next(w for w in API_WORKSPACES if w.name == "drive")
GH_WS = next(w for w in API_WORKSPACES if w.name == "gh")


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "t@example.test"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "Cli Test"], check=True)
    (path / "README.md").write_text("integration\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "commit", "-m", "init"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(path), "tag", "-a", "v0.0.0", "-m", "v0.0.0"],
        check=True,
        capture_output=True,
    )


def write_drive_config(config_dir: Path, *, tags_dir: Path, repo_path: Path) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.yaml").write_text(
        "backup:\n"
        f"  tags_dir: {tags_dir.resolve()}\n"
        "  repositories:\n"
        f"    - path: {repo_path.resolve()}\n",
        encoding="utf-8",
    )
    (config_dir / "drives.yaml").write_text(
        "drives:\n  google:\n    enabled: true\n    root: git-tags\n"
        "  onedrive:\n    enabled: false\n    root: ''\n"
        "  proton:\n    enabled: false\n    root: ''\n",
        encoding="utf-8",
    )


def _patch_notion_paths(monkeypatch: Any, task_root: Path, manifest: Path) -> None:
    for target in (
        "cli.commands.notion.notion_task_root",
        "cli.commands.notion.notion_pairs_file",
        "cli.services.notion_sync.notion_task_root",
        "cli.services.notion_sync.notion_pairs_file",
    ):
        if "pairs_file" in target:
            monkeypatch.setattr(target, lambda config_dir=None, m=manifest: m)
        else:
            monkeypatch.setattr(target, lambda config_dir=None, r=task_root: r)


@contextmanager
def notion_cli_context(monkeypatch: Any, tmp_path: Path) -> Iterator[Path]:
    task_root = copy_fixture_workspace(NOTION_WS, tmp_path, dest_name="notion-tasks")
    manifest = task_root / "tasks.pairs.json"
    pages = [notion_page(page_id="p1", title="✅ complete task")]
    _patch_notion_paths(monkeypatch, task_root, manifest)

    cfg_dir = tmp_path / "notion-config"
    cfg_dir.mkdir(exist_ok=True)
    (cfg_dir / "config.yaml").write_text(
        "notion:\n  database_id: db-integration\n  cleanup_before_deploy: false\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NOTION_TOKEN", "integration-token")
    monkeypatch.setenv("CLI_CONFIG_DIR", str(cfg_dir))

    with patch_notion_http(notion_cli_handler(pages)):
        yield task_root


@contextmanager
def notion_pairs_build_context(monkeypatch: Any, tmp_path: Path) -> Iterator[Path]:
    import shutil

    dest = tmp_path / "notion-pairs-clean"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(NOTION_CLI_WS, dest)
    manifest = dest / "tasks.pairs.json"
    _patch_notion_paths(monkeypatch, dest, manifest)
    monkeypatch.setenv("NOTION_TOKEN", "integration-token")
    yield dest


@contextmanager
def notion_orphan_context(monkeypatch: Any, tmp_path: Path) -> Iterator[Path]:
    """Task root with orphan header/body pairs (pairs build must fail)."""
    task_root = copy_fixture_workspace(NOTION_WS, tmp_path, dest_name="notion-orphans")
    manifest = task_root / "tasks.pairs.json"
    _patch_notion_paths(monkeypatch, task_root, manifest)
    monkeypatch.setenv("NOTION_TOKEN", "integration-token")
    yield task_root


@contextmanager
def notion_missing_manifest_context(monkeypatch: Any, tmp_path: Path) -> Iterator[Path]:
    empty = tmp_path / "notion-empty"
    empty.mkdir()
    (empty / "header").mkdir()
    (empty / "body").mkdir()
    _patch_notion_paths(monkeypatch, empty, empty / "tasks.pairs.json")
    monkeypatch.setenv("NOTION_TOKEN", "integration-token")
    yield empty


@contextmanager
def drive_cli_context(tmp_path: Path, *, broken: str | None = None) -> Iterator[tuple[Path, Path, str]]:
    repo = tmp_path / "demo-repo"
    repo.mkdir(exist_ok=True)
    tags_workspace = copy_fixture_workspace(DRIVE_WS, tmp_path)
    tags_dir = tags_workspace / "tags"
    config_dir = tmp_path / "config"
    write_drive_config(config_dir, tags_dir=tags_dir, repo_path=repo)
    provider = InMemoryDriveProvider()
    zip_path = tags_dir / "demo-repo" / "v0.0.0.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    zip_path.write_bytes(b"fixture zip")

    status_rows = [
        RepoBackupStatus(name="demo-repo", path=repo, git_tags=["v0.0.0"], downloaded=["v0.0.0"])
    ]
    ingest_rows = [(repo, SyncResult(created=["v0.0.0"], replaced=[], failed=[]))]
    sync_result = DriveSyncResult(
        ingest=ingest_rows,
        uploads=[("google", UploadResult(uploaded=["demo-repo/v1.0.0.zip"], skipped=[], failed=[]))],
    )
    snapshot = MagicMock()
    snapshot.summary_lines.return_value = ["branch: main"]

    from cli.services.backup_repository import resolve_repo_path as _real_resolve_repo_path

    def _resolve_repo_path(path: str | None = None):
        if path and path.startswith("/no/such"):
            return _real_resolve_repo_path(path)
        return repo

    def _providers(_selected: str | None = None):
        return [("google", provider, "remote/tags")]

    def _backup_status():
        if broken == "drive_status_error":
            raise RuntimeError("status failed")
        return status_rows

    def _ingest_repositories(*_args, **_kwargs):
        if broken == "drive_ingest_error":
            raise RuntimeError("ingest failed")
        return ingest_rows

    def _tags_dir_path():
        if broken == "missing_tags_dir":
            return tmp_path / "missing-tags"
        return tags_dir

    with (
        patch("cli.commands.drive._enabled_providers", _providers),
        patch("cli.commands.drive.backup_status", _backup_status),
        patch("cli.commands.drive.ingest_repositories", _ingest_repositories),
        patch("cli.commands.drive.sync_all", return_value=sync_result),
        patch("cli.commands.drive.resolve_repo_path", _resolve_repo_path),
        patch("cli.commands.drive.list_downloaded_tags", return_value=["v0.0.0", "v1.0.0"]),
        patch("cli.commands.drive.delete_repo_tag", return_value=zip_path),
        patch("cli.commands.drive.upload_missing", return_value=UploadResult(uploaded=["demo-repo/v1.0.0.zip"])),
        patch("cli.commands.drive.git_worktree_snapshot", return_value=snapshot),
        patch("cli.commands.drive.tags_dir_path", _tags_dir_path),
    ):
        yield config_dir, tags_dir, str(repo)


@contextmanager
def chrome_cli_context(
    tmp_path: Path,
    *,
    use_fixture: bool = True,
    skip_export: bool = False,
) -> Iterator[dict[str, str]]:
    workspace = copy_fixture_workspace(CHROME_WS, tmp_path)
    bookmarks = workspace / "data" / "bookmarks" / "bookmarks.html"
    bookmarks.parent.mkdir(parents=True, exist_ok=True)
    fixture_html = workspace / "Downloads" / "bookmarks.html"
    env = {
        **os.environ,
        "CLI_SKIP_CHROME_AUTOMATION": "1",
        "CLI_DOWNLOADS_DIR": str(workspace / "Downloads"),
        "CLI_BOOKMARKS_FILE": str(bookmarks),
        "CLI_ROOT": str(ROOT),
    }
    if use_fixture:
        env["CLI_BOOKMARKS_FIXTURE"] = str(fixture_html)
    else:
        empty_downloads = tmp_path / "empty-downloads"
        empty_downloads.mkdir(exist_ok=True)
        env["CLI_DOWNLOADS_DIR"] = str(empty_downloads)
        env["CLI_DOWNLOAD_TIMEOUT"] = "1"

    def _bookmarks_env() -> dict[str, str]:
        return env

    with (
        patch("cli.commands.chrome._bookmarks_env", _bookmarks_env),
        patch("cli.commands.chrome.bookmarks_file_path", lambda config_dir=None: bookmarks),
        patch("cli.commands.chrome.chrome_downloads_dir", lambda config_dir=None: workspace / "Downloads"),
    ):
        if skip_export and bookmarks.is_file():
            bookmarks.unlink()
        if use_fixture and not skip_export:
            subprocess.run(
                ["bash", str(ROOT / "scripts/chrome/export-bookmarks.sh")],
                env=env,
                check=True,
                cwd=ROOT,
            )
        yield env


def run_check_invoke(runner, check: CliApiCheck, *, env: dict[str, str] | None = None):
    from cli.cli import app

    merged = os.environ.copy()
    if env:
        merged.update(env)
    if check.extra_env:
        merged.update(check.extra_env)
    return runner.invoke(app, list(check.args), env=merged)


@contextmanager
def api_check_context(
    check: CliApiCheck,
    monkeypatch: Any,
    tmp_path: Path,
    *,
    gh_workspace: Path,
) -> Iterator[dict[str, str] | None]:
    """Apply mocks/env needed for one CliApiCheck (success or failure)."""
    env: dict[str, str] | None = None
    if check.api == "gh":
        if check.failure == "gh_auth":
            with patch_run_gh(side_effect=gh_auth_error()):
                yield env
        else:
            from tests.gh_harness import patch_gh_all

            with patch_gh_all(gh_workspace):
                yield env
        return

    if check.api == "notion":
        if check.failure == "missing_token":
            monkeypatch.delenv("NOTION_TOKEN", raising=False)
            with nullcontext():
                yield env
            return
        if check.failure == "missing_manifest":
            with notion_missing_manifest_context(monkeypatch, tmp_path):
                yield env
            return
        if check.failure == "notion_orphans":
            with notion_orphan_context(monkeypatch, tmp_path):
                yield env
            return
        if check.label == "notion pairs build":
            ctx = (
                notion_orphan_context(monkeypatch, tmp_path)
                if check.kind == "fail"
                else notion_pairs_build_context(monkeypatch, tmp_path)
            )
            with ctx:
                yield env
            return
        with notion_cli_context(monkeypatch, tmp_path):
            yield env
        return

    if check.api == "drive":
        broken = check.failure if check.failure in {
            "missing_tags_dir",
            "drive_ingest_error",
            "drive_status_error",
        } else None
        with drive_cli_context(tmp_path, broken=broken) as (config_dir, _tags, repo_path):
            env = {"CLI_CONFIG_DIR": str(config_dir)}
            if check.failure == "drive_bad_repo":
                check = check  # noqa: PLW0127 — args use /no/such/repo in registry
            yield env
        return

    if check.api == "chrome":
        use_fixture = check.failure != "chrome_no_fixture"
        skip_export = check.failure == "missing_bookmarks"
        with chrome_cli_context(
            tmp_path,
            use_fixture=use_fixture,
            skip_export=skip_export,
        ) as chrome_env:
            yield chrome_env
        return

    yield env


def run_cli_api_check(
    runner,
    check: CliApiCheck,
    monkeypatch: Any,
    tmp_path: Path,
    *,
    gh_workspace: Path,
) -> str | None:
    """Run one check; return error text or None when it passed."""
    with api_check_context(check, monkeypatch, tmp_path, gh_workspace=gh_workspace) as env:
        result = run_check_invoke(runner, check, env=env)
    output = result.stdout + (result.stderr or "")
    if result.exception is not None:
        output += f"\n{result.exception}"
    return validate_cli_api_check(check, exit_code=result.exit_code, output=output)


def run_cli_api_checks(
    checks: list[CliApiCheck],
    runner,
    monkeypatch: Any,
    tmp_path: Path,
    *,
    gh_workspace: Path,
) -> list[str]:
    errors: list[str] = []
    for check in checks:
        err = run_cli_api_check(runner, check, monkeypatch, tmp_path, gh_workspace=gh_workspace)
        if err:
            errors.append(f"{check.label}: {err}")
    return errors
