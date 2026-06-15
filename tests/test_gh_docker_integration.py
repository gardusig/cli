"""GitHub gh subcommands with mocked JSON (no real gh calls)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from shuttle.cli import app
from shuttle.integration.workspaces import API_WORKSPACES, fixture_dir
from tests.gh_harness import patch_gh_all

GH_WS = next(w for w in API_WORKSPACES if w.name == "gh")
RUNNER = CliRunner()


@pytest.mark.integration
def test_gh_issue_list_returns_fixture_json() -> None:
    with patch_gh_all(fixture_dir(GH_WS)):
        result = RUNNER.invoke(app, ["gh", "issue", "list"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload[0]["number"] == 42
    assert payload[0]["title"] == "Integration issue"


@pytest.mark.integration
def test_gh_issue_view_returns_fixture_body() -> None:
    with patch_gh_all(fixture_dir(GH_WS)):
        result = RUNNER.invoke(app, ["gh", "issue", "view", "42"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["body"] == "fixture body"
    assert payload["author"]["login"] == "test"
