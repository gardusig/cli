"""GitHub policy guards — blocked `gh` operations (exist in CLI, never execute)."""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TypeAlias

Matcher: TypeAlias = Callable[[Sequence[str]], bool]

MERGE_FORBIDDEN_MESSAGE = (
    "merge blocked: use GitHub UI or enable auto-merge on the PR.\n"
    "CLI does not merge PRs (policy). See docs/workflows.md#merge-policy"
)

PROJECTS_FORBIDDEN_MESSAGE = (
    "GitHub Projects blocked from CLI — use issues, labels, and backlog tree instead.\n"
    "See docs/gh.md#blocked-commands"
)

RULESET_FORBIDDEN_MESSAGE = (
    "GitHub Rulesets blocked from CLI — configure in the GitHub UI or repo settings.\n"
    "See docs/gh.md#blocked-commands"
)


class GhPolicyError(RuntimeError):
    """Base for CLI GitHub policy violations."""

    operation: str

    def __init__(self, message: str, *, operation: str) -> None:
        self.operation = operation
        super().__init__(message)


class MergeForbiddenError(GhPolicyError):
    """Raised when CLI merge is attempted."""

    def __init__(self) -> None:
        super().__init__(MERGE_FORBIDDEN_MESSAGE, operation="pr merge")


class ProjectsForbiddenError(GhPolicyError):
    """Raised when gh project commands are attempted via CLI."""

    def __init__(self) -> None:
        super().__init__(PROJECTS_FORBIDDEN_MESSAGE, operation="project")


class RulesetForbiddenError(GhPolicyError):
    """Raised when gh ruleset commands are attempted via CLI."""

    def __init__(self) -> None:
        super().__init__(RULESET_FORBIDDEN_MESSAGE, operation="ruleset")


@dataclass(frozen=True)
class BlockedGhOperation:
    """Registered `gh` argv prefix that must not run through the CLI provider."""

    id: str
    message: str
    doc: str
    matches: Matcher
    error_type: type[GhPolicyError]
    break_glass_env: str | None = None

    def raise_for(self) -> None:
        raise self.error_type()


def _is_pr_merge(args: Sequence[str]) -> bool:
    return len(args) >= 2 and args[0] == "pr" and args[1] == "merge"


def _is_project(args: Sequence[str]) -> bool:
    return len(args) >= 1 and args[0] == "project"


def _is_ruleset(args: Sequence[str]) -> bool:
    return len(args) >= 1 and args[0] == "ruleset"


BLOCKED_GH_OPERATIONS: tuple[BlockedGhOperation, ...] = (
    BlockedGhOperation(
        id="pr-merge",
        message=MERGE_FORBIDDEN_MESSAGE,
        doc="docs/workflows.md#merge-policy",
        matches=_is_pr_merge,
        error_type=MergeForbiddenError,
        break_glass_env="CLI_ALLOW_GH_MERGE",
    ),
    BlockedGhOperation(
        id="project",
        message=PROJECTS_FORBIDDEN_MESSAGE,
        doc="docs/gh.md#blocked-commands",
        matches=_is_project,
        error_type=ProjectsForbiddenError,
    ),
    BlockedGhOperation(
        id="ruleset",
        message=RULESET_FORBIDDEN_MESSAGE,
        doc="docs/gh.md#blocked-commands",
        matches=_is_ruleset,
        error_type=RulesetForbiddenError,
    ),
)

BLOCKED_BY_ID: dict[str, BlockedGhOperation] = {op.id: op for op in BLOCKED_GH_OPERATIONS}


def check_gh_args(args: Sequence[str]) -> None:
    """Raise policy error when argv matches a blocked operation."""
    for op in BLOCKED_GH_OPERATIONS:
        if not op.matches(args):
            continue
        if op.break_glass_env and os.environ.get(op.break_glass_env) == "1":
            return
        op.raise_for()


def policy_for_cli_command(group: str, subcommand: str | None = None) -> BlockedGhOperation | None:
    """Map Typer subcommand to blocked policy (for explicit CLI stubs)."""
    if group == "pr" and subcommand == "merge":
        return BLOCKED_BY_ID["pr-merge"]
    if group == "project":
        return BLOCKED_BY_ID["project"]
    if group == "ruleset":
        return BLOCKED_BY_ID["ruleset"]
    return None


def blocked_operations_catalog() -> list[dict[str, str]]:
    """Machine-readable list for docs/tests."""
    return [
        {
            "id": op.id,
            "gh_argv": {
                "pr-merge": "gh pr merge …",
                "project": "gh project …",
                "ruleset": "gh ruleset …",
            }.get(op.id, op.id),
            "cli": {
                "pr-merge": "cli gh pr merge N",
                "project": "cli gh project …",
                "ruleset": "cli gh ruleset …",
            }.get(op.id, f"cli gh {op.id}"),
            "alternative": {
                "pr-merge": "GitHub UI or PR auto-merge",
                "project": "cli gh backlog organize + priority:N labels",
                "ruleset": "GitHub repository/org settings UI",
            }.get(op.id, "GitHub web UI"),
            "doc": op.doc,
        }
        for op in BLOCKED_GH_OPERATIONS
    ]
