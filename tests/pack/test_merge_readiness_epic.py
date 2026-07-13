"""Pack tests — merge readiness for standalone gardusig-cli."""

from __future__ import annotations

from pathlib import Path

from tests.pack.conftest import requires_docs

ROOT = Path(__file__).resolve().parents[2]


@requires_docs
def test_merge_readiness_release_checklist() -> None:
    text = (ROOT / "docs" / "release.md").read_text(encoding="utf-8")
    assert "cli release main" in text
    assert "gardusig/cli" in text


def test_merge_readiness_repo_contract() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "https://github.com/gardusig/cli" in pyproject
    assert (ROOT / "src" / "commands" / "gh.py").is_file()


def test_merge_readiness_app_local_pipeline_config() -> None:
    pr_workflow = (ROOT / ".github" / "workflows" / "pull-request.yaml").read_text(encoding="utf-8")
    release_workflow = (ROOT / ".github" / "workflows" / "release.yaml").read_text(encoding="utf-8")
    assert (ROOT / "Dockerfile").is_file()
    assert (ROOT / ".dockerignore").is_file()
    assert not (ROOT / "docker").exists()
    workflows_dir = ROOT / ".github" / "workflows"
    workflow_files = sorted(path.name for path in workflows_dir.glob("*.yaml"))
    assert workflow_files == ["pull-request.yaml", "release.yaml"]
    assert (ROOT / "scripts" / "pull-request" / "version-check.sh").is_file()
    assert (ROOT / "scripts" / "release" / "pypi-release.sh").is_file()
    assert not (ROOT / "scripts" / "ci").exists()
    assert "scripts/pull-request/resolve-version.sh" in pr_workflow
    assert "timeout-minutes:" in pr_workflow
    assert "CI_UNIT_TIMEOUT" in pr_workflow
    assert "timeout-minutes:" in release_workflow


def test_merge_readiness_pack_smokes_present() -> None:
    pack = ROOT / "tests" / "pack"
    for name in (
        "test_release_epic.py",
        "test_chrome_photos_epic.py",
        "test_chrome_bookmarks_epic.py",
        "test_drive_sync_epic.py",
        "test_drive_providers_epic.py",
        "test_notion_epic.py",
        "test_merge_readiness_epic.py",
        "test_infra_epic.py",
    ):
        assert (pack / name).is_file(), name
