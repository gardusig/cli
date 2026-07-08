from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RequiredPath:
    path: str
    line_number: int


@dataclass(frozen=True)
class MissingPath:
    path: str
    target: Path
    line_number: int


@dataclass(frozen=True)
class WorkspacePathCheck:
    checked: int
    skipped: int
    missing: tuple[MissingPath, ...]


def load_required_paths(manifest: Path) -> tuple[RequiredPath, ...]:
    manifest = manifest.expanduser().resolve()
    paths: list[RequiredPath] = []

    manifest_lines = manifest.read_text(encoding="utf-8").splitlines()
    for line_number, raw_line in enumerate(manifest_lines, start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        path = line.strip("/")
        if path:
            paths.append(RequiredPath(path=path, line_number=line_number))

    return tuple(paths)


def check_workspace_paths(
    manifest: Path,
    *,
    workspace_root: Path,
    base: str | None = None,
    repo_root: Path | None = None,
) -> WorkspacePathCheck:
    required_paths = load_required_paths(manifest)
    workspace_root = workspace_root.expanduser().resolve()
    repo_root = (repo_root or Path(".")).expanduser().resolve()
    base = base.strip("/") if base else None

    checked = 0
    skipped = 0
    missing: list[MissingPath] = []

    for required in required_paths:
        target = _target_path(
            required.path,
            workspace_root=workspace_root,
            base=base,
            repo_root=repo_root,
        )
        if target is None:
            skipped += 1
            continue

        checked += 1
        if not target.exists():
            missing.append(
                MissingPath(
                    path=required.path,
                    target=target,
                    line_number=required.line_number,
                )
            )

    return WorkspacePathCheck(checked=checked, skipped=skipped, missing=tuple(missing))


def _target_path(
    path: str,
    *,
    workspace_root: Path,
    base: str | None,
    repo_root: Path,
) -> Path | None:
    if not base:
        return workspace_root / path

    if path == base:
        return repo_root

    prefix = f"{base}/"
    if path.startswith(prefix):
        return repo_root / path.removeprefix(prefix)

    return None
