"""Shared helpers for API docker integration tests (isolated copies, source guards)."""

from __future__ import annotations

import shutil
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from shuttle.integration.workspaces import ApiWorkspace, fixture_dir, protected_paths


def copy_fixture_workspace(workspace: ApiWorkspace, tmp_path: Path, *, dest_name: str | None = None) -> Path:
    """Copy tests/fixtures/<api>/workspace into a temp directory."""
    src = fixture_dir(workspace)
    if not src.is_dir():
        raise FileNotFoundError(f"fixture workspace missing: {src}")
    dest = tmp_path / (dest_name or f"{workspace.name}-workspace")
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    return dest


def snapshot_files(root: Path) -> set[Path]:
    """Relative paths of all files under root (for before/after guards)."""
    if not root.is_dir():
        return set()
    return {p.relative_to(root) for p in root.rglob("*") if p.is_file()}


def assert_tree_unchanged(root: Path, before: set[Path]) -> None:
    after = snapshot_files(root)
    assert before == after, f"protected tree changed under {root}"


def guard_protected_trees(workspace: ApiWorkspace) -> list[tuple[Path, set[Path]]]:
    """Snapshot protected repo paths before a mutating integration test."""
    return [(path, snapshot_files(path)) for path in protected_paths(workspace) if path.is_dir()]


def assert_protected_trees_unchanged(guards: list[tuple[Path, set[Path]]]) -> None:
    for path, before in guards:
        assert_tree_unchanged(path, before)


@contextmanager
def protected_repo_guard(workspace: ApiWorkspace) -> Iterator[list[tuple[Path, set[Path]]]]:
    guards = guard_protected_trees(workspace)
    yield guards
    assert_protected_trees_unchanged(guards)


def patch_config_paths(
    monkeypatch: Any,
    *,
    module: str,
    path_setters: dict[str, Callable[..., Path]],
) -> None:
    """Monkeypatch config path helpers in a service module."""
    for attr, factory in path_setters.items():
        target = f"{module}.{attr}"
        monkeypatch.setattr(target, factory)
