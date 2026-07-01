"""E2E: plan batch YAML → backlog tree → backlog next."""

from __future__ import annotations

import json
from pathlib import Path

from src.integration.workflow_runner import (
    invoke_workflow_cli,
    isolated_workflow_env,
    workflow_scratch,
)
from src.utils.config import project_root
from tests.harness.gh_harness import patch_gh_stateful


def check_plan_to_issues_workflow(git_root: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    scratch = workflow_scratch("plan-to-issues")
    env = isolated_workflow_env(scratch, "plan-to-issues")
    fixture = project_root() / "tests" / "fixtures" / "workflows" / "plan-to-issues"
    batch = fixture / "batch.yaml"
    gh_workspace = fixture / "gh"

    with patch_gh_stateful(gh_workspace) as store:
        code, output = invoke_workflow_cli(
            repo_root,
            None,
            ("gh", "--format", "json", "issue", "batch", "--file", str(batch), "--yes"),
            extra_env=env,
            mock_remote=False,
        )
        if code != 0:
            return [f"plan batch: exit {code}\n{output}"]
        if len(store.issues) != 3:
            errors.append(f"plan batch: expected 3 issues, got {len(store.issues)}")

        code, output = invoke_workflow_cli(
            repo_root,
            None,
            ("gh", "--format", "json", "backlog", "tree"),
            extra_env=env,
            mock_remote=False,
        )
        if code != 0:
            errors.append(f"backlog tree: exit {code}\n{output}")
            return errors
        tree = json.loads(output)
        children = tree.get("epics", {}).get("epic:wf-plan", [])
        if len(children) != 2:
            errors.append(f"backlog tree: expected 2 children under epic:wf-plan, got {len(children)}")

        code, output = invoke_workflow_cli(
            repo_root,
            None,
            ("gh", "--format", "json", "backlog", "next"),
            extra_env=env,
            mock_remote=False,
        )
        if code != 0:
            errors.append(f"backlog next: exit {code}\n{output}")
            return errors
        nxt = json.loads(output)
        if not nxt:
            errors.append("backlog next: expected a child issue, got empty result")
        elif "1.1" not in str(nxt.get("title", "")):
            errors.append(f"backlog next: expected lowest child title, got {nxt.get('title')!r}")

    return errors
