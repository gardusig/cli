"""E2E: gh issue context full extract."""

from __future__ import annotations

import json
from pathlib import Path

from src.integration.workflow_runner import (
    invoke_workflow_cli,
    isolated_workflow_env,
    workflow_scratch,
)
from src.integration.workspaces import API_WORKSPACES, fixture_dir
from tests.harness.gh_harness import patch_gh_stateful

_GH_WS = next(w for w in API_WORKSPACES if w.name == "gh")


def check_issue_context_workflow(git_root: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    scratch = workflow_scratch("issue-context")
    env = isolated_workflow_env(scratch)
    gh_workspace = fixture_dir(_GH_WS)

    with patch_gh_stateful(gh_workspace):
        code, output = invoke_workflow_cli(
            repo_root,
            None,
            ("gh", "--format", "json", "issue", "context", "2"),
            extra_env=env,
            mock_remote=False,
        )
        if code != 0:
            return [f"issue context: exit {code}\n{output}"]
        try:
            ctx = json.loads(output)
        except json.JSONDecodeError:
            return [f"issue context: invalid json\n{output}"]

        epic = ctx.get("epic") or {}
        parent = epic.get("parent") or {}
        if parent.get("number") != 1:
            errors.append(f"issue context: expected epic parent #1, got {parent!r}")
        if not ctx.get("siblings"):
            errors.append("issue context: expected siblings")
        if not ctx.get("comments"):
            errors.append("issue context: expected comments")
        if not ctx.get("linked_issues"):
            errors.append("issue context: expected linked_issues from body #3 ref")

    return errors
