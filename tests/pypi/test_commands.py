"""PyPI CLI commands (mocked service layer — real build in test_pypi_integration)."""

from __future__ import annotations

from tests.constants import ROOT

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from src.cli import app
from src.services.pypi_publish import TEST_REPOSITORY_URL, resolve_testpypi_token

runner = CliRunner()


@patch("src.commands.pypi.build_distributions")
def test_pypi_build(mock_build: MagicMock) -> None:
    mock_build.return_value = [Path("dist/src-1.0.0-py3-none-any.whl")]
    result = runner.invoke(app, ["pypi", "build", "--version", "1.0.0"])
    assert result.exit_code == 0
    assert "Built:" in result.stdout
    _, kwargs = mock_build.call_args
    assert kwargs["version"] == "1.0.0"


@patch("src.commands.pypi.verify_package_version_on_index")
@patch("src.commands.pypi.publish_distributions")
@patch("src.commands.pypi.build_distributions")
@patch("src.commands.pypi.resolve_pypi_token", return_value="tok")
@patch("src.commands.pypi.require_write_gate")
def test_pypi_upload(
    _gate: MagicMock,
    _token: MagicMock,
    mock_build: MagicMock,
    mock_upload: MagicMock,
    _verify: MagicMock,
) -> None:
    mock_build.return_value = [Path("dist/pkg.whl")]
    mock_upload.return_value = ["pkg.whl"]
    result = runner.invoke(app, ["pypi", "upload", "--yes", "--version", "1.0.0"])
    assert result.exit_code == 0
    assert "Published to PyPI" in result.stdout
    assert "Verified on PyPI" in result.stdout


@patch("src.commands.pypi.verify_package_version_on_index")
@patch("src.commands.pypi.publish_distributions")
@patch("src.commands.pypi.build_distributions")
@patch("src.commands.pypi.resolve_testpypi_token", return_value="test-token")
@patch("src.commands.pypi.require_write_gate")
def test_pypi_upload_testpypi_uses_test_index(
    _gate: MagicMock,
    _token: MagicMock,
    mock_build: MagicMock,
    mock_upload: MagicMock,
    mock_verify: MagicMock,
) -> None:
    mock_build.return_value = [Path("dist/pkg.whl")]
    mock_upload.return_value = ["pkg.whl"]
    result = runner.invoke(
        app,
        ["pypi", "upload", "--yes", "--testpypi", "--version", "1.0.0"],
    )

    assert result.exit_code == 0
    assert "Published to TestPyPI" in result.stdout
    _, kwargs = mock_upload.call_args
    assert kwargs["token"] == "test-token"
    assert kwargs["repository_url"] == TEST_REPOSITORY_URL
    mock_verify.assert_called_once_with("gardusig-cli", "1.0.0", testpypi=True)


@patch("src.commands.pypi.resolve_pypi_token", return_value="tok")
@patch("src.commands.pypi.require_write_gate")
def test_pypi_upload_skip_build_requires_existing_artifacts(
    _gate: MagicMock,
    _token: MagicMock,
    tmp_path: Path,
) -> None:
    result = runner.invoke(
        app,
        [
            "pypi",
            "upload",
            "--yes",
            "--skip-build",
            "--version",
            "1.0.0",
            "--dist-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "no artifacts" in result.stdout + (result.stderr or "")


def test_pypi_upload_invalid_version_reports_error() -> None:
    result = runner.invoke(app, ["pypi", "upload", "--yes", "--version", "bad"])

    assert result.exit_code != 0
    assert "release version must look like semver" in result.stdout + (result.stderr or "")


def test_resolve_testpypi_token_prefers_testpypi_env(monkeypatch) -> None:
    monkeypatch.setenv("PYPI_API_TOKEN", "prod-token")
    monkeypatch.setenv("TESTPYPI_API_TOKEN", "test-token")

    assert resolve_testpypi_token() == "test-token"


@patch("src.commands.pypi.build_distributions")
def test_publish_pypi_build_only_deprecated(mock_build: MagicMock) -> None:
    mock_build.return_value = [Path("dist/src-0.1.0-py3-none-any.whl")]
    result = runner.invoke(app, ["publish", "pypi", "--build-only"])
    assert result.exit_code == 0
    assert "Built:" in result.stdout


@patch("src.commands.pypi.assert_version_increased_vs_ref", return_value="0.1.1")
def test_pypi_version_check_ok(_assert: MagicMock) -> None:
    result = runner.invoke(app, ["pypi", "version", "check", "--base", "origin/main"])
    assert result.exit_code == 0
    assert "version ok" in result.stdout


@patch(
    "src.commands.pypi.assert_version_increased_vs_ref",
    side_effect=__import__(
        "src.services.pypi_publish", fromlist=["PyPiPublishError"]
    ).PyPiPublishError(
        "version 0.1.0 on this branch is not greater than origin/main (0.1.0). "
        "Bump pyproject.toml and src/__init__.py to at least '0.1.1'."
    ),
)
def test_pypi_version_check_fails(_assert: MagicMock) -> None:
    result = runner.invoke(app, ["pypi", "version", "check"])
    assert result.exit_code != 0
    assert "0.1.1" in (result.stdout + (result.stderr or ""))


@patch("src.commands.pypi.suggest_next_release_version", return_value="1.0.7")
def test_pypi_version_suggest(_suggest: MagicMock) -> None:
    result = runner.invoke(app, ["pypi", "version", "suggest"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "1.0.7"
    _suggest.assert_called_once()


@patch("src.commands.pypi.suggest_next_release_version", return_value="1.0.7")
def test_pypi_version_set_dry_run(_suggest: MagicMock) -> None:
    result = runner.invoke(app, ["pypi", "version", "set", "--dry-run"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "1.0.7"
    _suggest.assert_called_once()


@patch("src.commands.pypi.apply_next_release_version", return_value="1.0.7")
def test_pypi_version_set_writes(_apply: MagicMock) -> None:
    result = runner.invoke(app, ["pypi", "version", "set"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "1.0.7"
    _apply.assert_called_once()


@patch("src.commands.pypi.suggest_next_tag", return_value="v0.1.1")
@patch("src.commands.pypi.resolve_tag_policy")
@patch("src.services.git_shortcuts.GitShortcuts.all_tag_names", return_value=[])
def test_pypi_tag_suggest(_tags: MagicMock, _policy: MagicMock, _suggest: MagicMock) -> None:
    result = runner.invoke(app, ["pypi", "version", "tag-suggest"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "v0.1.1"
