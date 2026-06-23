"""Registry of API integration workspaces (fixtures + protected repo paths)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cli.utils.config import project_root


@dataclass(frozen=True)
class ApiWorkspace:
    """One public API surface under integration test."""

    name: str
    fixture_subpath: str
    protected_paths: tuple[str, ...]
    integration_module: str
    description: str = ""


def repo_root() -> Path:
    return project_root()


def fixture_dir(workspace: ApiWorkspace) -> Path:
    return repo_root() / "tests" / "fixtures" / workspace.fixture_subpath


def notion_task_fixture_dir() -> Path:
    """Minimal Notion task pair example for unit tests."""
    return repo_root() / "tests" / "fixtures" / "notion" / "tasks"


def protected_paths(workspace: ApiWorkspace) -> list[Path]:
    root = repo_root()
    return [root / rel for rel in workspace.protected_paths]


API_WORKSPACES: tuple[ApiWorkspace, ...] = (
    ApiWorkspace(
        name="notion",
        fixture_subpath="notion/workspace",
        protected_paths=(),
        integration_module="tests.test_notion_docker_integration",
        description="Task pairs: ingest → local files, deploy → Notion API",
    ),
    ApiWorkspace(
        name="chrome",
        fixture_subpath="chrome/workspace",
        protected_paths=(),
        integration_module="tests.test_chrome_docker_integration",
        description="Bookmarks: ingest from Downloads, deploy to local file",
    ),
    ApiWorkspace(
        name="drive",
        fixture_subpath="drive/workspace",
        protected_paths=(),
        integration_module="tests.test_drive_docker_integration",
        description="Tag zips: local ingest, mock cloud upload",
    ),
    ApiWorkspace(
        name="gh",
        fixture_subpath="gh/workspace",
        protected_paths=(),
        integration_module="tests.test_gh_docker_integration",
        description="GitHub CLI: mocked gh JSON for list/view",
    ),
)

INTEGRATION_TEST_MODULES: tuple[str, ...] = tuple(
    w.integration_module for w in API_WORKSPACES
) + (
    "tests.test_cli_api_integration",
    "tests.test_external_api_integration",
)
