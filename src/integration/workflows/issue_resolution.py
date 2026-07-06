"""E2E: epic issue refinement dry run and subissue PR planning."""

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


def check_issue_resolution_workflow(git_root: Path, repo_root: Path) -> list[str]:
    _ = git_root
    errors: list[str] = []
    scratch = workflow_scratch("issue-resolution")
    env = isolated_workflow_env(scratch)
    gh_workspace = fixture_dir(_GH_WS)

    with patch_gh_stateful(gh_workspace):
        code, output = invoke_workflow_cli(
            repo_root,
            None,
            ("craft", "--repo", "example/repo", "epic", "--number", "1", "--dry-run"),
            extra_env=env,
            mock_remote=False,
        )
        if code != 0:
            return [f"craft epic dry-run: exit {code}\n{output}"]
        epic = json.loads(output)
        if not epic.get("children"):
            errors.append("craft epic dry-run: expected subissues")
        if "Subissues / Closure checklist" not in str(epic.get("checklist_body", "")):
            errors.append("craft epic dry-run: missing closure checklist")

        code, output = invoke_workflow_cli(
            repo_root,
            None,
            ("craft", "--repo", "example/repo", "pr-plan", "--number", "2"),
            extra_env=env,
            mock_remote=False,
        )
        if code != 0:
            errors.append(f"craft pr-plan: exit {code}\n{output}")
            return errors
        plan = json.loads(output)
        if plan.get("issue") != 2:
            errors.append(f"craft pr-plan: expected issue 2, got {plan.get('issue')!r}")
        if not str(plan.get("branch", "")).startswith("craft/2-"):
            errors.append(f"craft pr-plan: unexpected branch {plan.get('branch')!r}")

    return errors
