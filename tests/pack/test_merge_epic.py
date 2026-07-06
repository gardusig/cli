"""Pack tests — mega-PR merge readiness (Epic 06c)."""

from __future__ import annotations

from pathlib import Path

import tomllib

from tests.pack.conftest import requires_docs

ROOT = Path(__file__).resolve().parents[2]


def test_merge_epic_version_is_1_0_3() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["version"] == "1.0.3"
    init = (ROOT / "src" / "__init__.py").read_text(encoding="utf-8")
    assert '__version__ = "1.0.3"' in init


def test_merge_epic_wheel_has_no_removed_script_data_files() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "tool.setuptools.data-files" not in text
    assert "src/scripts/_common.sh" not in text


@requires_docs
def test_merge_epic_release_docs() -> None:
    text = (ROOT / "docs" / "release.md").read_text(encoding="utf-8")
    assert "Pre-merge checklist" in text
    assert "cli release main --yes" in text
    assert "PR #20" in text or "pipelines PR #20" in text


@requires_docs
def test_merge_epic_hardening_pointer() -> None:
    text = (ROOT / "docs" / "public-cli-hardening.md").read_text(encoding="utf-8")
    assert "Merge readiness" in text
    assert "Epic 06c" in text or "merge & release" in text
    assert "PR #88" in text


@requires_docs
def test_merge_epic_closure_docs_exist() -> None:
    for path in (
        "docs/project.md",
        "docs/gh.md",
        "docs/docker.md",
        "docs/ci-workflows.md",
        "docs/hub-operator.md",
    ):
        assert (ROOT / path).is_file()
    gh = (ROOT / "docs" / "gh.md").read_text(encoding="utf-8")
    assert "Epic 11 closure" in gh
    project = (ROOT / "docs" / "project.md").read_text(encoding="utf-8")
    assert "Epic 08 closure" in project


def test_merge_epic_pack_smokes_present() -> None:
    pack = ROOT / "tests" / "pack"
    for name in (
        "test_project_epic.py",
        "test_gh_hub_epic.py",
        "test_docker_epic.py",
        "test_infra_epic.py",
        "test_hub_operator.py",
    ):
        assert (pack / name).is_file(), name


def test_merge_epic_integration_gate_script() -> None:
    script = ROOT / "tests" / "integration" / "check_integration_coverage.py"
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "integration_coverage" in text
