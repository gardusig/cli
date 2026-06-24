"""Repo hygiene: gitignore, requirements sync, no tracked build artifacts."""

from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

GITIGNORE_REQUIRED_PATTERNS = (
    ".venv/",
    ".integration-scratch/",
    "dist/",
    "gardusig_cli-*/",
    "cli-git-*/",
    "cli-public-*/",
    ".env",
)

UNTRACKED_PREFIXES = (
    ".integration-scratch/",
    "dist/",
    "build/",
    ".venv/",
    ".pytest_cache/",
    "gardusig_cli-",
    "gardusig_cli.egg-info/",
)


def _dependency_lines(path: Path) -> list[str]:
    lines: list[str] = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-r"):
            continue
        lines.append(line)
    return lines


def _normalize_dep(spec: str) -> str:
    return re.sub(r"[-_.]+", "-", spec.split("[")[0].strip().lower())


def test_gitignore_covers_local_artifacts() -> None:
    text = (ROOT / ".gitignore").read_text()
    for pattern in GITIGNORE_REQUIRED_PATTERNS:
        assert pattern in text, f".gitignore missing {pattern!r}"


def test_requirements_match_pyproject() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    runtime = {_normalize_dep(dep) for dep in data["project"]["dependencies"]}
    dev = {_normalize_dep(dep) for dep in data["project"]["optional-dependencies"]["dev"]}

    req_runtime = {_normalize_dep(line) for line in _dependency_lines(ROOT / "requirements.txt")}
    req_dev_only = {
        _normalize_dep(line)
        for line in _dependency_lines(ROOT / "requirements-dev.txt")
        if not line.startswith("-r")
    }

    assert req_runtime == runtime
    assert req_dev_only == dev


def test_build_artifacts_are_not_tracked() -> None:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    for path in result.stdout.splitlines():
        if not path:
            continue
        for prefix in UNTRACKED_PREFIXES:
            assert not path.startswith(prefix), f"tracked build artifact: {path}"


def test_docker_is_required_for_integration_checks(simulate_host_env: None) -> None:
    from gardusig_cli.integration.docker_guard import require_docker_integration

    with pytest.raises(RuntimeError, match="Docker"):
        require_docker_integration(context="hygiene test")
