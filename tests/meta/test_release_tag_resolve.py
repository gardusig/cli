"""Release tag resolution — git X.Y.Z → PyPI/Docker X.Y.Z."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.constants import ROOT


def test_resolve_tag_version_outputs_formats(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_REF_NAME", "2.5.0")
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "out.txt"))
    monkeypatch.chdir(ROOT)
    subprocess.run(["bash", "scripts/release/resolve-tag-version.sh"], check=True, cwd=ROOT)
    lines = dict(
        line.split("=", 1) for line in (tmp_path / "out.txt").read_text(encoding="utf-8").splitlines() if "=" in line
    )
    assert lines["git_tag"] == "2.5.0"
    assert lines["version"] == "2.5.0"
    assert lines["pypi_version"] == "2.5.0"
    assert lines["docker_tag"] == "2.5.0"


def test_resolve_tag_version_accepts_legacy_v_prefix(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_REF_NAME", "v2.5.0")
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "out.txt"))
    subprocess.run(["bash", "scripts/release/resolve-tag-version.sh"], check=True, cwd=ROOT)
    lines = dict(
        line.split("=", 1) for line in (tmp_path / "out.txt").read_text(encoding="utf-8").splitlines() if "=" in line
    )
    assert lines["git_tag"] == "v2.5.0"
    assert lines["version"] == "2.5.0"


def test_resolve_tag_version_rejects_non_semver(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_REF_NAME", "latest")
    result = subprocess.run(
        ["bash", "scripts/release/resolve-tag-version.sh"],
        cwd=ROOT,
        check=False,
    )
    assert result.returncode != 0
