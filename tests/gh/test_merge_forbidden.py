"""Merge forbid policy tests."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from src.cli import app
from src.providers.gh import GhProvider
from src.services.gh_policy import MergeForbiddenError
from src.services.gh_service import GhService


def test_gh_provider_blocks_pr_merge(monkeypatch) -> None:
    provider = GhProvider()
    monkeypatch.delenv("CLI_ALLOW_GH_MERGE", raising=False)
    with pytest.raises(MergeForbiddenError):
        provider.run(["pr", "merge", "1"])


def test_cli_gh_pr_merge_exits_nonzero() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["gh", "pr", "merge", "1", "--yes"])
    assert result.exit_code == 1
    assert "merge blocked" in result.output.lower() or "merge blocked" in (result.stderr or "").lower()


def test_gh_service_pr_merge_raises() -> None:
    svc = GhService(repo="gardusig/cli")
    with pytest.raises(MergeForbiddenError):
        svc.pr_merge(1)
