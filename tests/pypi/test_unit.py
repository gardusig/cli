"""PyPI version helpers (pure logic; no subprocess)."""

from __future__ import annotations

from tests.constants import ROOT

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.services.pypi_publish import (
    PyPiPublishError,
    apply_next_release_version,
    default_release_tag_name,
    fetch_latest_published_version,
    format_release_tag,
    normalize_release_version,
    read_project_version,
    resolve_release_version,
    suggest_next_release_version,
    sync_version_files,
    validate_release_tag_name,
)


def test_normalize_release_version_strips_v() -> None:
    assert normalize_release_version("v1.0.0") == "1.0.0"
    assert normalize_release_version("1.0.0") == "1.0.0"


def test_validate_release_tag_name_requires_v_prefix() -> None:
    assert validate_release_tag_name("v0.1.0") == "v0.1.0"
    with pytest.raises(PyPiPublishError, match="semver-v"):
        validate_release_tag_name("0.1.0")
    with pytest.raises(PyPiPublishError, match="semver-v"):
        validate_release_tag_name("2026-06-11")


def test_format_release_tag() -> None:
    assert format_release_tag("0.1.0") == "v0.1.0"
    assert format_release_tag("v1.2.3") == "v1.2.3"


def test_default_release_tag_name_reads_pyproject(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "x"\nversion = "0.2.5"\n', encoding="utf-8")
    assert default_release_tag_name(tmp_path) == "v0.2.5"


def test_normalize_release_version_rejects_invalid() -> None:
    with pytest.raises(PyPiPublishError, match="semver"):
        normalize_release_version("not-a-version")


def test_resolve_release_version_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLI_RELEASE_VERSION", "v2.3.4")
    assert resolve_release_version(None) == "2.3.4"


def test_sync_version_files_updates_pyproject_and_init(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "gardusig-cli"\nversion = "0.1.0"\n', encoding="utf-8")
    init_dir = tmp_path / "src"
    init_dir.mkdir()
    init_py = init_dir / "__init__.py"
    init_py.write_text('__version__ = "0.1.0"\n', encoding="utf-8")

    sync_version_files(tmp_path, "1.0.0")
    assert read_project_version(tmp_path) == "1.0.0"
    assert '__version__ = "1.0.0"' in init_py.read_text(encoding="utf-8")


def test_suggest_next_release_version_bumps_published() -> None:
    assert suggest_next_release_version(published="1.0.3") == "1.0.4"


def test_suggest_next_release_version_keeps_pyproject_on_first_release(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "x"\nversion = "1.0.6"\n', encoding="utf-8")
    assert suggest_next_release_version(published=None, root=tmp_path) == "1.0.6"


def test_suggest_next_release_version_defaults_when_missing_pyproject(tmp_path: Path) -> None:
    assert suggest_next_release_version(published=None, root=tmp_path) == "0.1.0"


def test_apply_next_release_version_writes_files(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "x"\nversion = "0.1.0"\n', encoding="utf-8")
    init_dir = tmp_path / "src"
    init_dir.mkdir()
    init_py = init_dir / "__init__.py"
    init_py.write_text('__version__ = "0.1.0"\n', encoding="utf-8")

    version = apply_next_release_version(published="1.0.0", root=tmp_path)
    assert version == "1.0.1"
    assert read_project_version(tmp_path) == "1.0.1"
    assert '__version__ = "1.0.1"' in init_py.read_text(encoding="utf-8")


@patch("src.services.pypi_publish.urllib.request.urlopen")
def test_fetch_latest_published_version_picks_highest(mock_urlopen: MagicMock) -> None:
    payload = {
        "releases": {
            "1.0.0": [{"url": "x"}],
            "1.0.2": [{"url": "x"}],
            "1.0.1": [{"url": "x"}],
        }
    }
    mock_urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(payload).encode()

    assert fetch_latest_published_version() == "1.0.2"


"""PyPI package metadata vs repo naming."""


import tomllib
from pathlib import Path


PYPROJECT = ROOT / "pyproject.toml"


def _project() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]


def test_pypi_distribution_name_is_src() -> None:
    assert _project()["name"] == "gardusig-cli"


def test_pypi_urls_point_at_cli_repo() -> None:
    urls = _project()["urls"]
    assert urls["Repository"] == "https://github.com/gardusig/cli"
    assert urls["Homepage"] == "https://github.com/gardusig/cli"
    assert urls["Issues"] == "https://github.com/gardusig/cli/issues"


def test_console_entrypoint_stays_cli() -> None:
    assert _project()["scripts"]["cli"] == "src.cli:run"


"""PyPI token resolution (unit; upload/build run in integration)."""


import pytest

from src.services.pypi_publish import PyPiPublishError, resolve_pypi_token


def test_resolve_pypi_token_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYPI_API_TOKEN", raising=False)
    with pytest.raises(PyPiPublishError, match="PYPI_API_TOKEN"):
        resolve_pypi_token()


def test_resolve_pypi_token_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYPI_API_TOKEN", "pypi-test-token")
    assert resolve_pypi_token() == "pypi-test-token"


"""PyPI / TestPyPI project page verification (unit)."""


import json
from unittest.mock import MagicMock, patch

import pytest

from src.services.pypi_publish import (
    PACKAGE_NAME,
    PyPiPublishError,
    package_index_json_url,
    verify_package_version_on_index,
)


def test_package_index_json_url_testpypi() -> None:
    assert package_index_json_url(PACKAGE_NAME, testpypi=True) == (
        "https://test.pypi.org/pypi/gardusig-cli/json"
    )


def test_package_index_json_url_production() -> None:
    assert package_index_json_url(PACKAGE_NAME, testpypi=False) == (
        "https://pypi.org/pypi/gardusig-cli/json"
    )


def test_verify_package_version_on_index_ok() -> None:
    payload = {
        "info": {"version": "1.0.0"},
        "releases": {"1.0.0": [{"filename": "src-1.0.0-py3-none-any.whl"}]},
    }
    body = json.dumps(payload).encode()
    response = MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = body
    with patch("src.services.pypi_publish.urllib.request.urlopen", return_value=response):
        verify_package_version_on_index(PACKAGE_NAME, "v1.0.0", testpypi=True)


def test_verify_package_version_on_index_missing_version() -> None:
    payload = {"info": {"version": "0.9.0"}, "releases": {"0.9.0": [{"filename": "x.whl"}]}}
    body = json.dumps(payload).encode()
    response = MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = body
    with (
        patch("src.services.pypi_publish.urllib.request.urlopen", return_value=response),
        patch("src.services.pypi_publish.time.sleep"),
    ):
        with pytest.raises(PyPiPublishError, match="not listed on TestPyPI"):
            verify_package_version_on_index(
                PACKAGE_NAME,
                "1.0.0",
                testpypi=True,
                retries=1,
            )


def test_verify_package_version_on_index_retries() -> None:
    import urllib.error

    ok_payload = {
        "info": {"version": "1.0.0"},
        "releases": {"1.0.0": [{"filename": "src-1.0.0-py3-none-any.whl"}]},
    }
    ok_body = json.dumps(ok_payload).encode()
    ok_response = MagicMock()
    ok_response.__enter__.return_value = ok_response
    ok_response.read.return_value = ok_body

    with (
        patch(
            "src.services.pypi_publish.urllib.request.urlopen",
            side_effect=[
                urllib.error.URLError("missing"),
                ok_response,
            ],
        ),
        patch("src.services.pypi_publish.time.sleep") as sleep,
    ):
        verify_package_version_on_index(PACKAGE_NAME, "1.0.0", testpypi=True, retries=2)
    sleep.assert_called_once()
