"""GitHub policy guards — merge forbid and related rules."""

from __future__ import annotations

MERGE_FORBIDDEN_MESSAGE = (
    "merge blocked: use GitHub UI or enable auto-merge on the PR.\n"
    "CLI does not merge PRs (policy). See docs/workflows.md#merge-policy"
)


class MergeForbiddenError(RuntimeError):
    """Raised when CLI merge is attempted."""

    def __init__(self) -> None:
        super().__init__(MERGE_FORBIDDEN_MESSAGE)
