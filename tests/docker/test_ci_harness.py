"""Docker integration harness checks for issue #9."""

from __future__ import annotations

from tests.constants import ROOT

from pathlib import Path


def test_docker_harness_files_exist() -> None:
    for rel in (
        "Dockerfile",
        ".dockerignore",
        "scripts/docker/common.sh",
    "scripts/docker/build-image.sh",
    "scripts/docker/build-images.sh",
    "scripts/docker/build-contest-image.sh",
        "scripts/docker/run-unit.sh",
        "scripts/docker/run-integration.sh",
        "scripts/test/unit.sh",
        "scripts/test/integration.sh",
        "scripts/test/smoke.sh",
        "tests/integration/check_integration_coverage.py",
        "tests/integration/check_public_commands.py",
        "tests/integration/check_public_endpoints.py",
        "tests/integration/check_docker_commands.py",
    ):
        path = ROOT / rel
        assert path.exists(), f"missing {rel}"
        assert path.stat().st_size > 0, f"empty {rel}"


def test_docker_harness_mentions_readonly_mount() -> None:
    common = (ROOT / "scripts/docker/common.sh").read_text()
    bootstrap = (ROOT / "scripts/docker/bootstrap.sh").read_text()
    assert ":ro" in common
    assert "/tmp/cli" in common
    assert "--exclude='.git'" in common
    assert "--exclude='.venv'" in common
    assert "--exclude='.env'" in common
    assert "CLI_DOCKER_SKIP_BUILD" in common
    assert "CLI_DOCKER_INTEGRATION=1" in common
    assert "CLI_INTEGRATION_SCRATCH=/tmp/integration-scratch" in common
    assert "docker.sock" in common
    assert "CLI_BOOTSTRAP_DEV" in bootstrap


def test_ci_workflow_runs_on_pull_request_only() -> None:
    workflow = (ROOT / ".github/workflows/test.yml").read_text()
    assert "pull_request:" in workflow
    assert "\n  push:" not in workflow
    assert "branches: [main]" not in workflow
    assert "unit:" in workflow or "name: Unit tests" in workflow
    assert "integration:" in workflow or "name: Integration tests" in workflow
    assert "needs: unit" in workflow
    assert "scripts/test/unit.sh" in workflow
    assert "scripts/test/integration.sh" in workflow


def test_release_workflow_runs_on_tags() -> None:
    workflow = (ROOT / ".github/workflows/release.yml").read_text()
    assert "tags:" in workflow
    assert "v*" in workflow
    assert "PYPI_API_TOKEN" in workflow
    assert "scripts/pypi/release.sh" in workflow
    assert "publish-pypi" in workflow
    assert "deploy-notion" not in workflow


def test_docker_smoke_runs_public_command_checker() -> None:
    smoke = (ROOT / "scripts/test/smoke.sh").read_text()
    assert "check_integration_coverage.py" in smoke
    assert "check_public_commands.py" in smoke
    assert "CLI_SKIP_CHROME_AUTOMATION=1" in smoke


def test_ci_workflow_runs_live_docker_in_container() -> None:
    workflow = (ROOT / ".github/workflows/test.yml").read_text()
    assert "scripts/test/integration.sh" in workflow
    assert "setup-python" not in workflow
    assert "bootstrap.sh" not in workflow


def test_public_command_registry_covers_all_commands() -> None:
    from gardusig_cli.integration.integration_coverage import assert_integration_coverage_gate

    assert_integration_coverage_gate()
