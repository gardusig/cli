"""Release deploy readiness — compare main to latest tag."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.services.git_shortcuts import GitShortcuts
from src.services.pypi_publish import PyPiPublishError
from src.services.tag_policy import latest_tag, resolve_tag_policy, suggest_next_tag


class GitDeployError(RuntimeError):
    """Deploy preflight failed."""


@dataclass(frozen=True)
class DeployAssessment:
    repo: str
    main_sha: str
    latest_tag: str | None
    tag_sha: str | None
    needs_tag: bool
    suggested_tag: str | None
    open_prs: tuple[dict[str, Any], ...] = ()

    @property
    def open_pr_count(self) -> int:
        return len(self.open_prs)

    def summary_lines(self) -> list[str]:
        lines = [
            f"repo: {self.repo}",
            f"main: {self.main_sha[:8]}",
        ]
        if self.latest_tag:
            tag_ref = self.tag_sha[:8] if self.tag_sha else "?"
            lines.append(f"tag: {self.latest_tag} ({tag_ref})")
        else:
            lines.append("tag: (none)")
        lines.append(f"needs_tag: {'yes' if self.needs_tag else 'no'}")
        if self.suggested_tag:
            lines.append(f"suggested: {self.suggested_tag}")
        return lines


def _resolved_tag_sha(svc: GitShortcuts, tag_name: str) -> str | None:
    return svc.tag_remote_sha(tag_name) or svc.tag_local_sha(tag_name)


def assess_deploy_readiness(
    svc: GitShortcuts,
    *,
    repo_root: Path,
    fetch: bool = True,
) -> DeployAssessment:
    """Read-only: is main ahead of the latest policy tag?"""
    if fetch:
        svc.fetch_all(prune=False)
    repo = repo_root.name
    main_sha = svc.main_tip_sha()
    all_tags = svc.all_tag_names()
    policy = resolve_tag_policy(repo_root, all_tags)
    latest = latest_tag(all_tags, policy)
    tag_sha = _resolved_tag_sha(svc, latest) if latest else None
    needs_tag = latest is None or tag_sha is None or main_sha != tag_sha
    suggested: str | None = None
    if needs_tag:
        try:
            suggested = suggest_next_tag(all_tags, policy, repo_root=repo_root)
        except PyPiPublishError:
            suggested = None
    return DeployAssessment(
        repo=repo,
        main_sha=main_sha,
        latest_tag=latest,
        tag_sha=tag_sha,
        needs_tag=needs_tag,
        suggested_tag=suggested,
        open_prs=(),
    )
