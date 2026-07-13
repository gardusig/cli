"""End-to-end workflow integration checks (git-only workflows)."""

from __future__ import annotations

from src.integration.workflow_runner import WorkflowCheckFn
from src.integration.workflows.reset_to_main import check_reset_to_main_workflow

WORKFLOW_REGISTRY: tuple[tuple[str, WorkflowCheckFn], ...] = (
    ("reset to main", check_reset_to_main_workflow),
)


def run_all_workflow_e2e_checks(repo_root, git_root) -> list[str]:
    errors: list[str] = []
    for label, fn in WORKFLOW_REGISTRY:
        result = fn(git_root, repo_root)
        if result:
            errors.append(f"workflow {label!r} failed:")
            errors.extend(result)
    return errors
