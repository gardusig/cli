"""Release tag resolution — git X.Y.Z → PyPI/Docker X.Y.Z."""

from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path

import pytest

from tests.constants import ROOT


def _project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def test_resolve_tag_version_outputs_formats(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    version = _project_version()
    monkeypatch.setenv("GITHUB_REF_NAME", version)
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "out.txt"))
    monkeypatch.chdir(ROOT)
    subprocess.run(["bash", "scripts/release/resolve-tag-version.sh"], check=True, cwd=ROOT)
    lines = dict(
        line.split("=", 1) for line in (tmp_path / "out.txt").read_text(encoding="utf-8").splitlines() if "=" in line
    )
    assert lines["git_tag"] == version
    assert lines["version"] == version
    assert lines["pypi_version"] == version
    assert lines["docker_tag"] == version


def test_resolve_tag_version_accepts_legacy_v_prefix(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    version = _project_version()
    monkeypatch.setenv("GITHUB_REF_NAME", f"v{version}")
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "out.txt"))
    subprocess.run(["bash", "scripts/release/resolve-tag-version.sh"], check=True, cwd=ROOT)
    lines = dict(
        line.split("=", 1) for line in (tmp_path / "out.txt").read_text(encoding="utf-8").splitlines() if "=" in line
    )
    assert lines["git_tag"] == f"v{version}"
    assert lines["version"] == version


def test_resolve_tag_version_rejects_tag_pyproject_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_REF_NAME", "99.99.99")
    result = subprocess.run(
        ["bash", "scripts/release/resolve-tag-version.sh"],
        cwd=ROOT,
        check=False,
    )
    assert result.returncode != 0


def test_resolve_tag_version_rejects_non_semver(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_REF_NAME", "latest")
    result = subprocess.run(
        ["bash", "scripts/release/resolve-tag-version.sh"],
        cwd=ROOT,
        check=False,
    )
    assert result.returncode != 0
