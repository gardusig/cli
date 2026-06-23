"""Docker integration harness checks for issue #9."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
        "scripts/test-unit.sh",
        "scripts/test-integration.sh",
        "scripts/integration-smoke.sh",
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
    bootstrap = (ROOT / "scripts/bootstrap.sh").read_text()
    assert ":ro" in common
    assert "/tmp/cli" in common
    assert "--exclude='.git'" in common
    assert "--exclude='.venv'" in common
    assert "CLI_DOCKER_SKIP_BUILD" in common
    assert "docker.sock" in common
    assert "CLI_BOOTSTRAP_DEV" in bootstrap


def test_ci_workflow_runs_on_push_and_pull_request() -> None:
    workflow = (ROOT / ".github/workflows/test.yml").read_text()
    assert "push:" in workflow
    assert "pull_request:" in workflow
    assert "branches: [main]" not in workflow
    assert "unit:" in workflow or "name: Unit tests" in workflow
    assert "integration:" in workflow or "name: Integration tests" in workflow
    assert "needs: unit" in workflow
    assert "test-unit.sh" in workflow
    assert "test-integration.sh" in workflow
    assert "cli:unit" in workflow
    assert "cli:integration" in workflow
    assert "target: unit" in workflow
    assert "target: integration" in workflow
    assert "cov-fail-under=80" in (ROOT / "scripts/docker/run-unit.sh").read_text()


def test_branch_protection_workflow_exists() -> None:
    path = ROOT / ".github/workflows/branch-protection.yml"
    text = path.read_text()
    assert path.is_file()
    assert "Unit tests (Docker)" in text
    assert "Integration tests (Docker)" in text
    assert "workflow_dispatch:" in text


def test_docker_smoke_runs_public_command_checker() -> None:
    smoke = (ROOT / "scripts/integration-smoke.sh").read_text()
    assert "check_integration_coverage.py" in smoke
    assert "check_public_commands.py" in smoke
    assert "CLI_SKIP_CHROME_AUTOMATION=1" in smoke


def test_ci_workflow_runs_live_docker_in_container() -> None:
    workflow = (ROOT / ".github/workflows/test.yml").read_text()
    assert "test-integration.sh" in workflow
    assert "setup-python" not in workflow
    assert "bootstrap.sh" not in workflow


def test_public_command_registry_covers_all_commands() -> None:
    from cli.integration.integration_coverage import assert_integration_coverage_gate

    assert_integration_coverage_gate()
