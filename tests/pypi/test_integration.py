"""PyPI build integration (real ``python -m build``, isolated workspace)."""

from __future__ import annotations

from tests.constants import ROOT

CI_CONFIG = ROOT / "config" / "ci"

import os
from pathlib import Path
from unittest.mock import patch
import zipfile

import pytest
from typer.testing import CliRunner

from src.cli import app
from src.services.pypi_publish import (
    PACKAGE_NAME,
    verify_package_version_on_index,
    build_distributions,
    read_project_version,
)
from tests.harness.pypi_harness import create_pypi_workspace, read_repo_version

runner = CliRunner()
TEST_VERSION = "1.0.0"


def _testpypi_token() -> str | None:
    token = os.environ.get("TESTPYPI_API_TOKEN", "").strip()
    return token or None


@pytest.fixture
def pypi_workspace() -> Path:
    return create_pypi_workspace()


@pytest.mark.integration
def test_build_distributions_writes_artifacts(pypi_workspace: Path) -> None:
    repo_version_before = read_repo_version()
    dist = pypi_workspace / "dist"
    artifacts = build_distributions(
        pypi_workspace,
        output_dir=dist,
        version=TEST_VERSION,
    )
    assert artifacts
    assert all(TEST_VERSION in path.name for path in artifacts)
    assert read_project_version(pypi_workspace) == TEST_VERSION
    assert read_repo_version() == repo_version_before


@pytest.mark.integration
def test_built_wheel_exposes_cli_install_contract(pypi_workspace: Path) -> None:
    artifacts = build_distributions(
        pypi_workspace,
        output_dir=pypi_workspace / "dist",
        version=TEST_VERSION,
    )
    wheels = [path for path in artifacts if path.suffix == ".whl"]
    assert wheels

    with zipfile.ZipFile(wheels[0]) as wheel:
        entry_points = wheel.read(
            f"gardusig_cli-{TEST_VERSION}.dist-info/entry_points.txt"
        ).decode()
        metadata = wheel.read(f"gardusig_cli-{TEST_VERSION}.dist-info/METADATA").decode()

    assert "cli = src.cli:run" in entry_points
    assert "Name: gardusig-cli" in metadata
    assert "Project-URL: Repository, https://github.com/gardusig/python-cli" in metadata


@pytest.mark.integration
def test_cli_pypi_build_command(pypi_workspace: Path) -> None:
    repo_version_before = read_repo_version()
    with patch("src.commands.pypi.project_root", return_value=pypi_workspace):
        result = runner.invoke(
            app,
            ["pypi", "build", "--version", TEST_VERSION],
            env={"CLI_CONFIG_DIR": str(CI_CONFIG)},
        )
    assert result.exit_code == 0, result.stdout + (result.stderr or "")
    assert "Built:" in result.stdout
    assert list((pypi_workspace / "dist").glob(f"*{TEST_VERSION}*"))
    assert read_repo_version() == repo_version_before


@pytest.mark.integration
def test_cli_pypi_upload_refuses_without_token(pypi_workspace: Path) -> None:
    build_distributions(pypi_workspace, version=TEST_VERSION)
    with patch("src.commands.pypi.project_root", return_value=pypi_workspace):
        result = runner.invoke(
            app,
            ["pypi", "upload", "--yes", "--skip-build", "--version", TEST_VERSION],
            env={"PYPI_API_TOKEN": ""},
        )
    assert result.exit_code != 0
    assert "PYPI_API_TOKEN" in result.stdout + (result.stderr or "")


@pytest.mark.integration
def test_release_publish_verifies_testpypi_project_page(pypi_workspace: Path) -> None:
    """Release path: build + upload to TestPyPI + verify project JSON page."""
    token = _testpypi_token()
    if token:
        with patch("src.commands.pypi.project_root", return_value=pypi_workspace):
            result = runner.invoke(
                app,
                [
                    "pypi",
                    "upload",
                    "--yes",
                    "--testpypi",
                    "--skip-existing",
                    "--version",
                    TEST_VERSION,
                ],
                env={
                    "TESTPYPI_API_TOKEN": token,
                    "CLI_RELEASE_VERSION": TEST_VERSION,
                    "CLI_CONFIG_DIR": str(CI_CONFIG),
                },
            )
        output = result.stdout + (result.stderr or "")
        assert result.exit_code == 0, output
        assert "Published to TestPyPI" in output
        assert f"Verified on TestPyPI: {PACKAGE_NAME}=={TEST_VERSION}" in output
        return

    with (
        patch("src.commands.pypi.project_root", return_value=pypi_workspace),
        patch("src.commands.pypi.publish_distributions", return_value=["pkg.whl"]) as mock_publish,
        patch("src.commands.pypi.verify_package_version_on_index") as mock_verify,
        patch("src.commands.pypi.build_distributions") as mock_build,
    ):
        mock_build.return_value = [pypi_workspace / "dist" / f"src-{TEST_VERSION}-py3-none-any.whl"]
        (pypi_workspace / "dist").mkdir(parents=True, exist_ok=True)
        result = runner.invoke(
            app,
            [
                "pypi",
                "upload",
                "--yes",
                "--testpypi",
                "--skip-existing",
                "--version",
                TEST_VERSION,
            ],
            env={
                "PYPI_API_TOKEN": "pypi-test-token",
                "CLI_RELEASE_VERSION": TEST_VERSION,
                "CLI_CONFIG_DIR": str(CI_CONFIG),
            },
        )
    output = result.stdout + (result.stderr or "")
    assert result.exit_code == 0, output
    mock_publish.assert_called_once()
    mock_verify.assert_called_once_with(PACKAGE_NAME, TEST_VERSION, testpypi=True)
    assert f"Verified on TestPyPI: {PACKAGE_NAME}=={TEST_VERSION}" in output


@pytest.mark.integration
def test_testpypi_project_page_json_api() -> None:
    """Live TestPyPI JSON API: verify indexed release when token set, else smoke the endpoint."""
    if _testpypi_token():
        verify_package_version_on_index(PACKAGE_NAME, TEST_VERSION, testpypi=True)
        return

    import json
    import urllib.error
    import urllib.request

    from src.services.pypi_publish import package_index_json_url

    url = package_index_json_url(PACKAGE_NAME, testpypi=True)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return  # package not published to TestPyPI in this environment
        raise AssertionError(f"TestPyPI project page HTTP {exc.code}: {url}") from exc
    except urllib.error.URLError as exc:
        raise AssertionError(f"TestPyPI project page unreachable: {url}") from exc
    assert data["info"].get("name") == PACKAGE_NAME
    assert "releases" in data
