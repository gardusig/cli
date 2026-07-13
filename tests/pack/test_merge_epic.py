"""Pack tests — mega-PR merge readiness (Epic 06c)."""

from __future__ import annotations

from pathlib import Path

import tomllib

from tests.pack.conftest import requires_docs

ROOT = Path(__file__).resolve().parents[2]


def test_merge_epic_version_is_1_0_6() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["version"] == "1.0.6"
    init = (ROOT / "src" / "__init__.py").read_text(encoding="utf-8")
    assert '__version__ = "1.0.6"' in init


def test_merge_epic_wheel_has_no_removed_script_data_files() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "tool.setuptools.data-files" not in text
    assert "src/scripts/_common.sh" not in text


@requires_docs
def test_merge_epic_release_docs() -> None:
    text = (ROOT / "docs" / "release.md").read_text(encoding="utf-8")
    assert "cli release main" in text


@requires_docs
def test_merge_epic_closure_docs_exist() -> None:
    for path in (
        "docs/docker.md",
        "docs/ci-workflows.md",
    ):
        assert (ROOT / path).is_file()


def test_merge_epic_pack_smokes_present() -> None:
    pack = ROOT / "tests" / "pack"
    for name in (
        "test_docker_epic.py",
        "test_infra_epic.py",
        "test_merge_readiness_epic.py",
    ):
        assert (pack / name).is_file(), name


def test_merge_epic_integration_gate_script() -> None:
    script = ROOT / "tests" / "integration" / "check_integration_coverage.py"
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "integration_coverage" in text
