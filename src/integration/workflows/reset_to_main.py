"""E2E: nested dirty branches → git reset --yes --delete-merged."""

from __future__ import annotations

import subprocess
from pathlib import Path

from src.integration.public_endpoints import dirty_integration_git, reset_integration_git
from src.integration.workflow_integration import (
    _assert_branches,
    _assert_on_synced_main,
    _current_branch,
    _is_dirty,
    _local_branches,
    setup_nested_merged_branches,
)
from src.integration.workflow_runner import (
    invoke_workflow_cli,
    isolated_workflow_env,
    workflow_scratch,
)


def _git(git_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(git_root), *args],
        capture_output=True,
        text=True,
        check=True,
    )


def check_reset_to_main_workflow(git_root: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    scratch = workflow_scratch("reset-main")
    env = isolated_workflow_env(scratch)

    reset_integration_git(git_root)
    merged_b, unmerged = setup_nested_merged_branches(git_root)
    _git(git_root, "checkout", unmerged)
    dirty_integration_git(git_root)
    if not _is_dirty(git_root) or merged_b not in _local_branches(git_root):
        return ["reset workflow setup: expected dirty tree on nested tip"]

    code, output = invoke_workflow_cli(
        repo_root,
        git_root,
        ("git", "reset", "--yes", "--delete-merged"),
        extra_env=env,
    )
    if code != 0:
        errors.append(f"reset to main workflow: exit {code}\n{output}")
        return errors
    if "reset" not in output:
        errors.append(f"reset to main workflow: missing success message\n{output}")
        return errors
    _assert_on_synced_main(git_root, errors, prefix="reset to main workflow")
    _assert_branches(
        git_root,
        errors,
        prefix="reset to main workflow",
        gone={"feature-a", merged_b},
        kept={unmerged},
    )
    if _current_branch(git_root) != "main":
        errors.append("reset to main workflow: expected checkout on main")
    return errors
