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
    assert (ROOT / "docker" / "pull-request.dockerfile").is_file()
    assert (ROOT / "docker" / "release.dockerfile").is_file()
    pr_docker = (ROOT / "docker" / "pull-request.dockerfile").read_text(encoding="utf-8")
    release_docker = (ROOT / "docker" / "release.dockerfile").read_text(encoding="utf-8")
    assert "COPY src src" in pr_docker
    assert "COPY src src" in release_docker
    assert "COPY . ." not in pr_docker
    assert "COPY . ." not in release_docker
    assert "COPY scripts/ scripts/" in pr_docker
    assert "COPY scripts/pull-request scripts/pull-request" not in pr_docker
    assert "COPY scripts/release scripts/release" not in pr_docker
    workflows_dir = ROOT / ".github" / "workflows"
    workflow_files = sorted(path.name for path in workflows_dir.glob("*.yaml"))
    assert workflow_files == ["pull-request.yaml", "release.yaml"]
    assert (ROOT / "scripts" / "pull-request" / "version-check.sh").is_file()
    assert (ROOT / "scripts" / "release" / "pypi-release.sh").is_file()
    assert not (ROOT / "scripts" / "ci").exists()
    assert "PR_DOCKERFILE: docker/pull-request.dockerfile" in pr_workflow
    assert "RELEASE_DOCKERFILE: docker/release.dockerfile" in release_workflow
    assert "bash scripts/" not in pr_workflow
    assert "bash scripts/" not in release_workflow
    assert ".sh" not in pr_workflow
    assert ".sh" not in release_workflow
    assert "scripts/" not in pr_workflow
    assert "scripts/" not in release_workflow
    assert "docker build -f" in pr_workflow
    assert "docker build -f" in release_workflow
    assert "--target resolve" in pr_workflow
    assert "--target resolve" in release_workflow
    assert "version-check" in pr_workflow
    assert "testpypi" not in pr_workflow
    assert "testpypi-consumer" not in pr_workflow
    assert "publish-testpypi" in release_workflow
    assert "testpypi-consumer" in release_workflow
    assert "needs: version-check" in pr_workflow
    assert "needs: resolve" in pr_workflow
    assert "tags:" in release_workflow
    assert '"*"' in release_workflow
    assert 'if: github.ref == \'refs/heads/main\'' not in release_workflow
    assert "publish-pypi" in release_workflow
    assert "publish-docker" in release_workflow
    assert "publish-github" in release_workflow
    assert "docker-release" not in release_workflow
    assert "timeout-minutes:" in pr_workflow


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
