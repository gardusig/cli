"""PyPI token resolution (unit; upload/build run in integration)."""

from __future__ import annotations

import pytest

from gardusig_cli.services.pypi_publish import PyPiPublishError, resolve_pypi_token


def test_resolve_pypi_token_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYPI_API_TOKEN", raising=False)
    with pytest.raises(PyPiPublishError, match="PYPI_API_TOKEN"):
        resolve_pypi_token()


def test_resolve_pypi_token_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYPI_API_TOKEN", "pypi-test-token")
    assert resolve_pypi_token() == "pypi-test-token"
