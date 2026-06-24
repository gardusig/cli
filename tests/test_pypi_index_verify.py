"""PyPI / TestPyPI project page verification (unit)."""

from __future__ import annotations

import io
import json
from unittest.mock import MagicMock, patch

import pytest

from cli.services.pypi_publish import (
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
        "releases": {"1.0.0": [{"filename": "gardusig_cli-1.0.0-py3-none-any.whl"}]},
    }
    body = json.dumps(payload).encode()
    response = MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = body
    with patch("cli.services.pypi_publish.urllib.request.urlopen", return_value=response):
        verify_package_version_on_index(PACKAGE_NAME, "v1.0.0", testpypi=True)


def test_verify_package_version_on_index_missing_version() -> None:
    payload = {"info": {"version": "0.9.0"}, "releases": {"0.9.0": [{"filename": "x.whl"}]}}
    body = json.dumps(payload).encode()
    response = MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = body
    with (
        patch("cli.services.pypi_publish.urllib.request.urlopen", return_value=response),
        patch("cli.services.pypi_publish.time.sleep"),
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
        "releases": {"1.0.0": [{"filename": "gardusig_cli-1.0.0-py3-none-any.whl"}]},
    }
    ok_body = json.dumps(ok_payload).encode()
    ok_response = MagicMock()
    ok_response.__enter__.return_value = ok_response
    ok_response.read.return_value = ok_body

    with (
        patch(
            "cli.services.pypi_publish.urllib.request.urlopen",
            side_effect=[
                urllib.error.HTTPError("url", 404, "missing", {}, io.BytesIO(b"")),
                ok_response,
            ],
        ),
        patch("cli.services.pypi_publish.time.sleep") as sleep,
    ):
        verify_package_version_on_index(PACKAGE_NAME, "1.0.0", testpypi=True, retries=2)
    sleep.assert_called_once()
