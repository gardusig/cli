"""Pack tests — Epic 06d–06g merge readiness (PR #96)."""

from __future__ import annotations

from pathlib import Path

from tests.pack.conftest import requires_docs

ROOT = Path(__file__).resolve().parents[2]

@requires_docs
def test_merge_readiness_release_checklist() -> None:
    text = (ROOT / "docs" / "release.md").read_text(encoding="utf-8")
    assert "PR #96 merge" in text
    assert "Epic 06d" in text or "06d–06g" in text or "06d-06g" in text
    assert "cli gh wf run" in text or "gh wf" in text
    assert "gardusig/cli" in text
    assert "pipelines #38" in text
    for issue in ("#50", "#27", "#28", "#31", "#30", "#29"):
        assert issue in text
    assert "#20" in text and "#23" in text
    assert "#12" in text and "#15" in text


@requires_docs
def test_merge_readiness_hardening_section() -> None:
    text = (ROOT / "docs" / "public-cli-hardening.md").read_text(encoding="utf-8")
    assert "Epic 06e" in text
    assert "Merge readiness" in text
    assert "PR #96" in text
    assert "156/156" in text or "156" in text
    assert "Epic 06g" in text
    assert "Shipped" in text


def test_merge_readiness_repo_rename_contract() -> None:
    repos = (ROOT / "config" / "gh" / "repos.yaml").read_text(encoding="utf-8")
    assert "repository: gardusig/cli" in repos
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "https://github.com/gardusig/cli" in pyproject
    assert (ROOT / "src" / "commands" / "gh_wf.py").is_file()


def test_merge_readiness_app_local_pipeline_config() -> None:
    pr_config = (ROOT / ".github" / "pull-request.yaml").read_text(encoding="utf-8")
    assert "repo: gardusig/cli" in pr_config
    assert "docker/python-cli.dockerfile" in pr_config
    caller = (ROOT / ".github" / "workflows" / "pull-request.yml").read_text(encoding="utf-8")
    assert "gardusig/yaml/.github/workflows/pull-request.yml@main" in caller
    assert "repo_slug: cli" in caller
    assert "repository: gardusig/cli" in caller


@requires_docs
def test_merge_readiness_hub_operator_rename_note() -> None:
    hub = (ROOT / "docs" / "hub-operator.md").read_text(encoding="utf-8")
    assert "gardusig/cli" in hub
    assert "gardusig/python-cli" in hub
    assert "cli gh wf" in hub or "gh wf run" in hub


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
