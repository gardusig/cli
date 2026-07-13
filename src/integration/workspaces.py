"""Registry of API integration workspaces (fixtures + protected repo paths)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.utils.config import project_root


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
        integration_module="tests.notion.test_docker_integration",
        description="Task pairs: ingest → local files, deploy → Notion API",
    ),
    ApiWorkspace(
        name="chrome",
        fixture_subpath="chrome/workspace",
        protected_paths=(),
        integration_module="tests.chrome.test_docker_integration",
        description="Bookmarks: ingest from Downloads, deploy to local file",
    ),
    ApiWorkspace(
        name="drive",
        fixture_subpath="drive/workspace",
        protected_paths=(),
        integration_module="tests.drive.test_docker_integration",
        description="Tag zips: local ingest, mock cloud upload",
    ),
    ApiWorkspace(
        name="contest",
        fixture_subpath="contest/toy",
        protected_paths=(),
        integration_module="tests.contest.test_docker_integration",
        description="Contest validate: mocked Docker runner (no live daemon)",
    ),
)

INTEGRATION_TEST_MODULES: tuple[str, ...] = tuple(
    w.integration_module for w in API_WORKSPACES
) + (
    "tests.cli.test_api_integration",
    "tests.cli.test_endpoint_integration",
    "tests.meta.test_external_api_integration",
    "tests.pypi.test_integration",
    "tests.workflows.test_workflow_e2e",
)

WORKFLOW_MODULES: tuple[str, ...] = ("tests.workflows.test_workflow_e2e",)
