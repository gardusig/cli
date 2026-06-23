"""PyPI packaging helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cli.services.pypi_publish import (
    PyPiPublishError,
    build_distributions,
    publish_distributions,
    resolve_pypi_token,
)


def test_resolve_pypi_token_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYPI_API_TOKEN", raising=False)
    with pytest.raises(PyPiPublishError, match="PYPI_API_TOKEN"):
        resolve_pypi_token()


def test_resolve_pypi_token_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYPI_API_TOKEN", "pypi-test-token")
    assert resolve_pypi_token() == "pypi-test-token"


@patch("cli.services.pypi_publish.subprocess.run")
def test_build_distributions_invokes_build(mock_run: MagicMock, tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()

    def _fake_build(*_args, **_kwargs):
        (dist / "gardusig_cli-0.1.0-py3-none-any.whl").write_bytes(b"x")
        return MagicMock(returncode=0)

    mock_run.side_effect = _fake_build
    artifacts = build_distributions(tmp_path, output_dir=dist)
    assert artifacts[0].name.endswith(".whl")
    assert mock_run.call_args.args[0][1:3] == ["-m", "build"]


@patch("cli.services.pypi_publish.subprocess.run")
def test_publish_distributions_uses_token(mock_run: MagicMock, tmp_path: Path) -> None:
    wheel = tmp_path / "pkg.whl"
    wheel.write_bytes(b"x")
    mock_run.return_value = MagicMock(returncode=0)
    names = publish_distributions([wheel], token="pypi-secret")
    assert names == ["pkg.whl"]
    env = mock_run.call_args.kwargs["env"]
    assert env["TWINE_USERNAME"] == "__token__"
    assert env["TWINE_PASSWORD"] == "pypi-secret"
