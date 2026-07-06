"""End-to-end workflow integration checks (one major test per user workflow)."""

from __future__ import annotations

from src.integration.workflow_runner import WorkflowCheckFn
from src.integration.workflows.dirty_branch_to_pr import check_dirty_branch_to_pr_workflow
from src.integration.workflows.issue_context import check_issue_context_workflow
from src.integration.workflows.issue_resolution import check_issue_resolution_workflow
from src.integration.workflows.plan_to_issues import check_plan_to_issues_workflow
from src.integration.workflows.reset_to_main import check_reset_to_main_workflow

WORKFLOW_REGISTRY: tuple[tuple[str, WorkflowCheckFn], ...] = (
    ("plan to issues", check_plan_to_issues_workflow),
    ("issue context extract", check_issue_context_workflow),
    ("issue resolution", check_issue_resolution_workflow),
    ("dirty branch to pr", check_dirty_branch_to_pr_workflow),
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
