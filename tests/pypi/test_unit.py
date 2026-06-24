"""PyPI version helpers (pure logic; no subprocess)."""

from __future__ import annotations

from tests.constants import ROOT

from pathlib import Path

import pytest

from src.services.pypi_publish import (
    PyPiPublishError,
    normalize_release_version,
    read_project_version,
    resolve_release_version,
    sync_version_files,
)


def test_normalize_release_version_strips_v() -> None:
    assert normalize_release_version("v1.0.0") == "1.0.0"
    assert normalize_release_version("1.0.0") == "1.0.0"


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


import io
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
                urllib.error.HTTPError("url", 404, "missing", {}, io.BytesIO(b"")),
                ok_response,
            ],
        ),
        patch("src.services.pypi_publish.time.sleep") as sleep,
    ):
        verify_package_version_on_index(PACKAGE_NAME, "1.0.0", testpypi=True, retries=2)
    sleep.assert_called_once()
