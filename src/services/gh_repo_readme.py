"""Sync gardusig profile README from GitHub repo list."""

from __future__ import annotations

import re
from pathlib import Path

from src.services.gh_service import GhService

START_MARKER = "<!-- repos:auto:start -->"
END_MARKER = "<!-- repos:auto:end -->"


def format_repo_lines(owner: str, repos: list[dict[str, str]]) -> str:
    """Render a simple markdown bullet list of public repositories."""
    lines: list[str] = []
    for repo in repos:
        name = repo["name"]
        url = repo.get("url") or f"https://github.com/{owner}/{name}"
        description = (repo.get("description") or "").strip()
        if description:
            lines.append(f"- [{name}]({url}) — {description}")
        else:
            lines.append(f"- [{name}]({url})")
    return "\n".join(lines)


def render_readme_section(owner: str, repos: list[dict[str, str]]) -> str:
    body = format_repo_lines(owner, repos)
    return f"{START_MARKER}\n{body}\n{END_MARKER}"


def patch_readme(readme: Path, owner: str, repos: list[dict[str, str]]) -> str:
    """Return updated README text; raise if markers are missing."""
    text = readme.read_text(encoding="utf-8")
    if START_MARKER not in text or END_MARKER not in text:
        raise ValueError(
            f"README missing sync markers ({START_MARKER} / {END_MARKER}): {readme}"
        )
    section = render_readme_section(owner, repos)
    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        flags=re.DOTALL,
    )
    return pattern.sub(section, text, count=1)


def sync_profile_readme(
    readme: Path,
    *,
    owner: str = "gardusig",
    limit: int = 100,
) -> tuple[str, list[dict[str, str]]]:
    """Query public repos and build updated README contents."""
    svc = GhService()
    repos = svc.repo_list(owner=owner, limit=limit, visibility="public")
    updated = patch_readme(readme, owner, repos)
    return updated, repos
