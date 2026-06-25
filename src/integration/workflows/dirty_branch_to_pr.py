"""E2E: dirty feature branch → git push --yes → gh pr create --yes."""

from __future__ import annotations

import subprocess
from pathlib import Path

from src.integration.public_endpoints import (
    FEATURE_BRANCH,
    dirty_integration_git,
    reset_integration_git,
    setup_feature_branch,
)
from src.integration.workflow_runner import (
    invoke_workflow_cli,
    isolated_workflow_env,
    workflow_scratch,
)
from src.integration.workspaces import API_WORKSPACES, fixture_dir
from tests.harness.gh_harness import patch_gh_stateful

_GH_WS = next(w for w in API_WORKSPACES if w.name == "gh")


def _git(git_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(git_root), *args],
        capture_output=True,
        text=True,
        check=True,
    )


def _latest_commit_message(git_root: Path) -> str:
    return _git(git_root, "log", "-1", "--format=%s").stdout.strip()


def check_dirty_branch_to_pr_workflow(git_root: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    scratch = workflow_scratch("dirty-pr")
    env = isolated_workflow_env(scratch)
    gh_workspace = fixture_dir(_GH_WS)

    reset_integration_git(git_root)
    setup_feature_branch(git_root, "checked_out")
    dirty_integration_git(git_root)

    with patch_gh_stateful(gh_workspace) as store:
        code, output = invoke_workflow_cli(
            repo_root,
            git_root,
            ("git", "push", "--yes", "-m", "workflow pr push"),
            extra_env=env,
        )
        if code != 0:
            return [f"dirty push: exit {code}\n{output}"]
        if "pushed" not in output:
            errors.append(f"dirty push: missing success message\n{output}")
        if _git(git_root, "branch", "--show-current").stdout.strip() != FEATURE_BRANCH:
            errors.append("dirty push: expected to stay on feature branch")
        if _latest_commit_message(git_root) != "workflow pr push":
            errors.append("dirty push: expected commit on feature branch")

        code, output = invoke_workflow_cli(
            repo_root,
            git_root,
            (
                "gh",
                "--format",
                "json",
                "pr",
                "create",
                "--title",
                "Workflow integration PR",
                "--body",
                "From dirty branch workflow test.",
                "--yes",
            ),
            extra_env=env,
        )
        if code != 0:
            errors.append(f"pr create: exit {code}\n{output}")
            return errors
        if not store.pr_create_calls:
            errors.append("pr create: expected gh pr create invocation")
        if "example/repo/pull/8" not in output:
            errors.append(f"pr create: missing PR url in output\n{output}")

    return errors
