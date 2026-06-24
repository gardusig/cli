"""Registry checks for API integration workspaces."""

from __future__ import annotations

from cli.integration.workspaces import API_WORKSPACES, fixture_dir, protected_paths


def test_every_api_workspace_has_fixture_tree() -> None:
    for workspace in API_WORKSPACES:
        path = fixture_dir(workspace)
        assert path.is_dir(), f"missing fixture for {workspace.name}: {path}"


def test_protected_paths_exist_when_declared() -> None:
    for workspace in API_WORKSPACES:
        if not workspace.protected_paths:
            continue
        for path in protected_paths(workspace):
            assert path.is_dir(), f"protected path missing for {workspace.name}: {path}"


def test_integration_modules_are_unique() -> None:
    modules = [w.integration_module for w in API_WORKSPACES]
    assert len(modules) == len(set(modules))
