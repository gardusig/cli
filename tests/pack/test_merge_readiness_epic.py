"""Pack tests — merge readiness and in-repo CI contract."""

from __future__ import annotations

from pathlib import Path

from tests.pack.conftest import requires_docs

ROOT = Path(__file__).resolve().parents[2]


@requires_docs
def test_merge_readiness_release_checklist() -> None:
    text = (ROOT / "docs" / "release.md").read_text(encoding="utf-8")
    assert "Pre-merge checklist" in text
    assert "Post-merge release" in text
    assert "gardusig/cli" in text
    assert "version-check" in text
    assert "unit-test" in text
    assert "pypi-test" in text
    assert "integration-test" in text


@requires_docs
def test_merge_readiness_hardening_section() -> None:
    text = (ROOT / "docs" / "public-cli-hardening.md").read_text(encoding="utf-8")
    assert "Registry contracts" in text
    assert "Verification" in text
    assert "Dockerfile" in text or "integration-test" in text


def test_merge_readiness_repo_rename_contract() -> None:
    repos = (ROOT / "config" / "gh" / "repos.yaml").read_text(encoding="utf-8")
    assert "repository: gardusig/cli" in repos
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "https://github.com/gardusig/cli" in pyproject
    runtime = (ROOT / "src" / "services" / "pipeline_runtime.py").read_text(encoding="utf-8")
    assert '"gardusig/cli": "gardusig/python-cli"' in runtime


def test_merge_readiness_app_local_pipeline_config() -> None:
    pr_workflow = (ROOT / ".github" / "workflows" / "pull-request.yaml").read_text(encoding="utf-8")
    assert "pull_request:" in pr_workflow
    assert "docker build" in pr_workflow
    assert "--target version-check" in pr_workflow
    assert "--target unit-test" in pr_workflow
    assert "--target pypi-test" in pr_workflow
    assert "--target integration-test" in pr_workflow
    assert "--target testpypi-consumer" in pr_workflow
    assert "timeout-minutes: 5" in pr_workflow
    release_workflow = (ROOT / ".github" / "workflows" / "release.yaml").read_text(encoding="utf-8")
    assert "tags:" in release_workflow
    assert "--target release" in release_workflow
    assert "--target pypi-consumer" in release_workflow


@requires_docs
def test_merge_readiness_hub_operator_rename_note() -> None:
    hub = (ROOT / "docs" / "hub-operator.md").read_text(encoding="utf-8")
    assert "gardusig/cli" in hub


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
    ):
        assert (pack / name).is_file(), name
