"""Inventory of docs, scripts, and CLI entrypoints for `cli links`."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.utils.config import project_root


@dataclass(frozen=True)
class CatalogEntry:
    label: str
    cli: str | None = None
    script: str | None = None
    doc: str | None = None
    note: str | None = None


QUICK_DEFAULTS = (
    ("git start", "issue start: align main + branch (wip-YYMMDD-NNN or issue slug); --no-prep to branch in place"),
    ("git commit", "message defaults to '.'"),
    ("git push", "add + commit + push; on main starts random branch — use --yes -y to skip prompt"),
    ("git reset", "return to synced main; optional --delete-merged or interactive branch cleanup — --yes"),
    ("git stash push", "message defaults to '.'"),
    ("git tag", "sync main, tag with per-repo pattern (.cli/tag.yaml)"),
    ("git deploy", "tag main when ahead of latest tag and no open PRs block release"),
    ("git zip", "zip a vX.Y.Z tag into iCloud git-tags/REPO/"),
    ("drive status", "git tags vs zips in backup.tags_dir (iCloud)"),
    ("drive ingest", "zip all tags for configured repos into git-tags/"),
    ("drive upload", "deploy missing zips to cloud replicas"),
    ("drive deploy", "deploy missing zips to all replicas (cloud + USB)"),
    ("drive sync", "ingest all repositories, then deploy to replicas"),
    ("chrome bookmarks ingest", "Chrome → local HTML (chrome.bookmarks_file)"),
    ("chrome bookmarks deploy", "local HTML → Chrome"),
    ("notion pairs build", "scan header/ + body/ → tasks.pairs.json"),
    ("notion ingest", "Notion → local task pairs"),
    ("notion deploy", "local task pairs → Notion board"),
    ("notion sync", "ingest from Notion, then deploy local tasks"),
)

# Lifecycle shortcuts: command → shell wrapper + doc (see docs/workflows.md).
WORKFLOW_SHORTCUTS: tuple[tuple[str, str, str, str], ...] = (
    ("git reset", "reset.sh", "docs/workflows.md", "return to synced main + prune branches"),
    ("git start", "start.sh", "docs/workflows.md", "issue start: align main + named branch"),
    ("git push", "push.sh", "docs/workflows.md", "push current branch; start on main"),
)

WORKFLOW_CHAIN = (
    "backlog next → reset → start → push → review → pr create → [UI merge] → issue close → reset"
)

QUICK_DEFAULT_SCRIPTS: dict[str, str] = {
    "git start": "scripts/git/start.sh",
    "git commit": "scripts/git/commit.sh",
    "git push": "scripts/git/push.sh",
    "git reset": "scripts/git/reset.sh",
    "git stash push": "scripts/git/stash.sh",
    "git tag": "scripts/git/tag.sh",
}


GIT_SCRIPT_COMMANDS: tuple[tuple[str, str], ...] = (
    ("branch.sh", "git branch list"),
    ("branch-list.sh", "git branch list"),
    ("branch-current.sh", "git branch current"),
    ("branch-prune.sh", "git branch prune"),
    ("branch-rename.sh", "git branch rename"),
    ("branch-clear.sh", "git branch clear"),
    ("branch-delete.sh", "git branch delete"),
    ("branch-delete-merged.sh", "git branch delete --merged"),
    ("branch-delete-all.sh", "git branch delete --all"),
    ("cherry-pick.sh", "git cherry pick"),
    ("clean.sh", "git clean"),
    ("commit.sh", "git commit"),
    ("docs.sh", "git docs"),
    ("large-files.sh", "git large files"),
    ("main.sh", "git main"),
    ("post-merge-cleanup.sh", "git post merge cleanup"),
    ("pull.sh", "git pull"),
    ("push.sh", "git push"),
    ("rebase.sh", "git rebase"),
    ("reset.sh", "git reset"),
    ("revert.sh", "git revert"),
    ("review.sh", "git review"),
    ("start.sh", "git start"),
    ("stash.sh", "git stash"),
    ("tag.sh", "git tag"),
    ("deploy.sh", "git deploy"),
    ("tag-list.sh", "git tag list"),
    ("tag-push.sh", "git tag push"),
    ("zip.sh", "git zip"),
)

GH_SCRIPT_COMMANDS: tuple[tuple[str, str], ...] = (
    ("backlog-next.sh", "gh backlog next"),
    ("backlog-tree.sh", "gh backlog tree"),
    ("backlog-resequence.sh", "gh backlog resequence"),
    ("issue-list.sh", "gh issue list"),
    ("issue-view.sh", "gh issue view"),
    ("issue-context.sh", "gh issue context"),
    ("issue-search.sh", "gh issue search"),
    ("issue-create.sh", "gh issue create"),
    ("issue-edit.sh", "gh issue edit"),
    ("issue-close.sh", "gh issue close"),
    ("issue-comment.sh", "gh issue comment"),
    ("issue-batch.sh", "gh issue batch"),
    ("label-list.sh", "gh label list"),
    ("sync-labels.sh", "gh label sync"),
    ("labelize-backlog.sh", "gh issue batch"),
    ("pr-list.sh", "gh pr list"),
    ("pr-view.sh", "gh pr view"),
    ("pr-diff.sh", "gh pr diff"),
    ("pr-create.sh", "gh pr create"),
    ("pr-edit.sh", "gh pr edit"),
    ("pr-close.sh", "gh pr close"),
    ("pr-merge.sh", "gh pr merge (blocked — policy)"),
    ("project.sh", "gh project (blocked — policy)"),
    ("ruleset.sh", "gh ruleset (blocked — policy)"),
    ("repo-view.sh", "gh repo view"),
)

CHROME_SCRIPTS: tuple[tuple[str, str], ...] = (
    ("ingest.sh", "bookmarks ingest — Chrome → local"),
    ("deploy.sh", "bookmarks deploy — local → Chrome"),
    ("export.sh", "export bookmarks HTML to configured path"),
    ("import.sh", "import bookmarks HTML into Chrome"),
    ("wait-download.sh", "poll Downloads for newest HTML export"),
)

TOP_LEVEL_COMMANDS: tuple[tuple[str, str], ...] = (
    ("git / g", "git shortcuts (see cli git --help)"),
    ("gh", "GitHub via gh — issues, labels, PRs, backlog (see docs/gh.md)"),
    ("opencode", "AI entry point — chat, gh flows, raw prompts (see docs/opencode.md)"),
    ("test", "Run repo test pipeline (unit / integration / all)"),
    ("deploy", "Deploy pipeline wrapper"),
    ("release", "Release build pipeline wrapper"),
    ("restore", "restore workflows (placeholder)"),
    ("drive", "git-tags local store (iCloud) + cloud upload — status, ingest, upload"),
    ("chrome", "Chrome browser — bookmarks ingest / deploy"),
    ("notion", "Notion task board — pairs build / ingest / deploy / sync / cleanup"),
    ("links", "this index — docs, scripts, defaults"),
    ("docker", "monitor + cleanup — stats, top, stop, delete, reset (see cli docker --help)"),
)

DOCKER_QUICK_DEFAULTS: tuple[tuple[str, str], ...] = (
    ("docker stats", "top consumers by cpu, memory, or storage"),
    ("docker top", "dashboard across cpu, memory, and storage"),
    ("docker reset", "stop all, delete containers, prune images + cache — --yes"),
    ("docker stop", "stop running containers — --yes"),
    ("docker container-delete", "remove containers — --yes"),
    ("docker image-delete", "prune unused images — --yes"),
)

DOCKER_SCRIPT_COMMANDS: tuple[tuple[str, str], ...] = (
    ("stats.sh", "docker stats"),
    ("reset.sh", "docker reset"),
    ("stop.sh", "docker stop"),
    ("container-delete.sh", "docker container-delete"),
    ("image-delete.sh", "docker image-delete"),
)

DOCKER_QUICK_DEFAULT_SCRIPTS: dict[str, str] = {
    "docker reset": "scripts/docker/reset.sh",
    "docker stop": "scripts/docker/stop.sh",
    "docker container-delete": "scripts/docker/container-delete.sh",
    "docker image-delete": "scripts/docker/image-delete.sh",
    "docker stats": "scripts/docker/stats.sh",
}


def doc_entries(root: Path | None = None) -> list[CatalogEntry]:
    base = root or project_root()
    docs_dir = base / "docs"
    entries: list[CatalogEntry] = []
    readme = base / "README.md"
    if readme.is_file():
        entries.append(CatalogEntry("Root README", doc=str(readme.relative_to(base))))
    if docs_dir.is_dir():
        for path in sorted(docs_dir.rglob("*.md")):
            rel = path.relative_to(base)
            entries.append(CatalogEntry(path.stem.replace("-", " ").title(), doc=str(rel)))
    return entries


def git_script_entries(root: Path | None = None) -> list[CatalogEntry]:
    base = root or project_root()
    git_dir = base / "scripts" / "git"
    entries: list[CatalogEntry] = []
    for script_name, cli_cmd in GIT_SCRIPT_COMMANDS:
        script_path = git_dir / script_name
        rel = str(script_path.relative_to(base)) if script_path.is_file() else None
        entries.append(
            CatalogEntry(
                script_name.replace(".sh", "").replace("-", " "),
                cli=f"cli {cli_cmd}",
                script=rel,
                doc="docs/git.md",
            )
        )
    return entries


def gh_script_entries(root: Path | None = None) -> list[CatalogEntry]:
    base = root or project_root()
    gh_dir = base / "scripts" / "gh"
    entries: list[CatalogEntry] = []
    for script_name, cli_cmd in GH_SCRIPT_COMMANDS:
        script_path = gh_dir / script_name
        rel = str(script_path.relative_to(base)) if script_path.is_file() else None
        entries.append(
            CatalogEntry(
                script_name.replace(".sh", "").replace("-", " "),
                cli=f"cli {cli_cmd}",
                script=rel,
                doc="docs/gh.md",
            )
        )
    return entries


def chrome_script_entries(root: Path | None = None) -> list[CatalogEntry]:
    base = root or project_root()
    chrome_dir = base / "scripts" / "chrome"
    entries: list[CatalogEntry] = []
    for script_name, note in CHROME_SCRIPTS:
        script_path = chrome_dir / script_name
        rel = str(script_path.relative_to(base)) if script_path.is_file() else None
        entries.append(
            CatalogEntry(
                script_name.replace(".sh", "").replace("-", " "),
                script=rel,
                doc="docs/bookmarks.md",
                note=note,
            )
        )
    return entries
