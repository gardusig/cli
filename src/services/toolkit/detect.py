from __future__ import annotations

import subprocess
from pathlib import Path

from src.services.toolkit.catalog import REPO_LANGUAGE_PROFILES, lint_languages

IGNORED_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".pytest_cache", "dist", "build"}


class ToolkitDetectionError(RuntimeError):
    pass


def confirm_markers(workspace: Path, markers: tuple[str, ...]) -> None:
    if not markers:
        return
    root = workspace.expanduser().resolve()
    if not root.exists():
        raise ToolkitDetectionError(f"workspace does not exist: {root}")
    if any(_has_marker(root, marker) for marker in markers):
        return
    joined = ", ".join(markers)
    raise ToolkitDetectionError(f"workspace does not look like the requested project type (missing one of: {joined})")


def repo_languages(workspace: Path) -> tuple[str, ...]:
    root = workspace.expanduser().resolve()
    profile = _repo_profile(root)
    if profile:
        present = tuple(language for language in profile if _language_present(root, language))
        return present or profile
    detected = tuple(language for language in lint_languages() if _language_present(root, language))
    return detected or ("markdown",)


def _repo_profile(root: Path) -> tuple[str, ...] | None:
    remote = _origin_repo_name(root)
    if remote and remote in REPO_LANGUAGE_PROFILES:
        return REPO_LANGUAGE_PROFILES[remote]
    return REPO_LANGUAGE_PROFILES.get(root.name)


def _origin_repo_name(root: Path) -> str | None:
    result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    url = result.stdout.strip().removesuffix(".git")
    if not url:
        return None
    return url.rsplit("/", maxsplit=1)[-1].split(":", maxsplit=1)[-1]


def _language_present(root: Path, language: str) -> bool:
    if language == "markdown":
        return _has_marker(root, "*.md") or _has_marker(root, "*.mdx")
    if language == "python":
        return any((root / marker).exists() for marker in ("pyproject.toml", "setup.py", "requirements.txt")) or _has_marker(root, "*.py")
    if language == "typescript":
        return (root / "package.json").is_file()
    if language == "cpp":
        return (root / "CMakeLists.txt").is_file() or _has_marker(root, "*.cpp")
    if language == "shell":
        return _has_marker(root, "*.sh")
    if language == "java":
        return any((root / marker).exists() for marker in ("pom.xml", "build.gradle", "build.gradle.kts"))
    return False


def _has_marker(root: Path, marker: str) -> bool:
    if any(char in marker for char in "*?["):
        return any(True for _ in _iter_glob(root, marker))
    return (root / marker).exists()


def _iter_glob(root: Path, pattern: str):
    for path in root.rglob(pattern):
        rel_parts = path.relative_to(root).parts
        if any(part in IGNORED_DIRS for part in rel_parts):
            continue
        yield path

