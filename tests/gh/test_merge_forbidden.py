"""GitHub policy — blocked merge, issue close, and rulesets."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from src.cli import app
from src.providers.gh import GhProvider
from src.services.gh_policy import (
    MergeForbiddenError,
    RulesetForbiddenError,
    blocked_operations_catalog,
    check_gh_args,
)
from src.services.gh_service import GhService


def test_gh_provider_blocks_pr_merge(monkeypatch) -> None:
    provider = GhProvider()
    monkeypatch.delenv("CLI_ALLOW_GH_MERGE", raising=False)
    with pytest.raises(MergeForbiddenError):
        provider.run(["pr", "merge", "1"])


def test_gh_provider_allows_pr_merge_break_glass(monkeypatch) -> None:
    monkeypatch.setenv("CLI_ALLOW_GH_MERGE", "1")
    check_gh_args(["pr", "merge", "1"])


def test_cli_gh_pr_merge_exits_nonzero() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["gh", "pr", "merge", "1", "--yes"])
    assert result.exit_code == 1
    assert "merge blocked" in (result.output + (result.stderr or "")).lower()


def test_cli_gh_ruleset_list_blocked() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["gh", "ruleset", "list"])
    assert result.exit_code == 1
    assert "rulesets blocked" in (result.output + (result.stderr or "")).lower()


def test_cli_gh_policy_list_json() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["gh", "policy", "list"])
    assert result.exit_code == 0
    assert "pr-merge" in result.output
    assert "issue-close" in result.output
    assert "project" not in result.output


def test_gh_service_pr_merge_raises() -> None:
    svc = GhService(repo="gardusig/cli")
    with pytest.raises(MergeForbiddenError):
        svc.pr_merge(1)


def test_check_gh_args_ruleset() -> None:
    with pytest.raises(RulesetForbiddenError):
        check_gh_args(["ruleset", "view", "1"])


def test_blocked_catalog_covers_merge_issue_close_and_rulesets() -> None:
    ids = {row["id"] for row in blocked_operations_catalog()}
    assert {"pr-merge", "issue-close", "ruleset"} <= ids
