"""Inventory of docs and CLI entrypoints for `cli links`."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.utils.config import project_root


@dataclass(frozen=True)
class CatalogEntry:
    label: str
    cli: str | None = None
    doc: str | None = None
    note: str | None = None


QUICK_DEFAULTS = (
    ("ship", "stage, commit ('.'), push main — personal backup flow"),
    ("git start", "issue start: align main + branch (wip-YYMMDD-NNN or issue slug); --no-prep to branch in place"),
    ("git commit", "message defaults to '.'"),
    ("git push", "add + commit + push; on main pushes main by default — use --branch for wip flow; --yes -y to skip prompt"),
    ("git reset", "return to synced main; optional --delete-merged or interactive branch cleanup — --yes"),
    ("git stash push", "message defaults to '.'"),
    ("git tag", "sync main, tag with per-repo pattern (config/tag.yaml)"),
    ("git deploy", "tag main when ahead of latest tag and no open PRs block release"),
    ("git zip", "zip a vX.Y.Z tag into iCloud git-tags/REPO/"),
    ("drive status", "git tags vs zips in backup.tags_dir (iCloud)"),
    ("drive ingest", "zip all tags for configured repos into git-tags/"),
    ("drive upload", "deploy missing zips to cloud replicas (--dry-run, --format json)"),
    ("drive download", "restore missing remote zips into local git-tags hub"),
    ("drive deploy", "deploy missing zips to all replicas (cloud + USB)"),
    ("drive sync", "ingest all repositories, then deploy to replicas"),
    ("chrome bookmarks ingest", "exported HTML → configured local backup"),
    ("chrome bookmarks merge", "append new bookmark URLs (dedupe by URL)"),
    ("chrome bookmarks snapshot", "timestamped safety copy"),
    ("chrome bookmarks deploy", "validate backup for browser import"),
    ("notion pairs build", "scan header/ + body/ → tasks.pairs.json"),
    ("notion ingest", "Notion → local task pairs"),
    ("notion deploy", "local task pairs → Notion board"),
    ("notion sync", "ingest from Notion, then deploy local tasks"),
    ("project list", "inspect GitHub Projects v2 boards"),
    ("project spawn", "batch-create issues from YAML seed file"),
    ("project pairs build", "scan local recurrence pairs manifest"),
    ("project deploy", "push local pairs to GitHub Project + issues"),
    ("project ingest", "pull board/issue state into local headers"),
    ("project sync", "ingest then deploy project pairs"),
    ("tasks run notion deploy", "shortcut for notion deploy --yes"),
    ("tasks ingest-pr", "ingest tasks and open a database PR"),
    ("contest validate", "two-tier Docker validation for fast/brute/gen"),
    ("pypi version check", "PR gate: branch version must be greater than origin/main"),
    ("pypi upload --testpypi", "TestPyPI dry-run publish; production uses release main"),
    ("release main", "guarded production release: tag, PyPI publish, verify, GitHub release"),
)

# Lifecycle shortcuts: command + doc (see docs/workflows.md).
WORKFLOW_SHORTCUTS: tuple[tuple[str, str, str], ...] = (
    ("git reset", "docs/workflows.md", "return to synced main + prune branches"),
    ("git start", "docs/workflows.md", "issue start: align main + named branch"),
    ("git push", "docs/workflows.md", "push current branch; start on main"),
)

WORKFLOW_CHAIN = (
    "backlog next → reset → start → push → review → pr create → [UI merge] → issue close → reset"
)

GIT_COMMANDS: tuple[tuple[str, str], ...] = (
    ("branch", "git branch list"),
    ("branch list", "git branch list"),
    ("branch current", "git branch current"),
    ("branch prune", "git branch prune"),
    ("branch rename", "git branch rename"),
    ("branch clear", "git branch clear"),
    ("branch delete", "git branch delete"),
    ("branch delete merged", "git branch delete --merged"),
    ("branch delete all", "git branch delete --all"),
    ("cherry pick", "git cherry pick"),
    ("clean", "git clean"),
    ("commit", "git commit"),
    ("docs", "git docs"),
    ("large files", "git large files"),
    ("main", "git main"),
    ("post merge cleanup", "git post merge cleanup"),
    ("pull", "git pull"),
    ("push", "git push"),
    ("rebase", "git rebase"),
    ("reset", "git reset"),
    ("revert", "git revert"),
    ("review", "git review"),
    ("start", "git start"),
    ("stash", "git stash"),
    ("tag", "git tag"),
    ("deploy", "git deploy"),
    ("tag list", "git tag list"),
    ("tag push", "git tag push"),
    ("zip", "git zip"),
)

GH_COMMANDS: tuple[tuple[str, str], ...] = (
    ("backlog next", "gh backlog next"),
    ("backlog tree", "gh backlog tree"),
    ("backlog resequence", "gh backlog resequence"),
    ("issue list", "gh issue list"),
    ("issue view", "gh issue view"),
    ("issue context", "gh issue context"),
    ("issue search", "gh issue search"),
    ("issue create", "gh issue create"),
    ("issue edit", "gh issue edit"),
    ("issue close", "gh issue close"),
    ("issue reopen", "gh issue reopen"),
    ("issue comment", "gh issue comment"),
    ("issue status", "gh issue status"),
    ("issue batch", "gh issue batch"),
    ("label list", "gh label list"),
    ("label sync", "gh label sync"),
    ("labelize backlog", "gh issue batch"),
    ("pr list", "gh pr list"),
    ("pr view", "gh pr view"),
    ("pr diff", "gh pr diff"),
    ("pr shortcut", "gh pr"),
    ("pr create", "gh pr create"),
    ("pr edit", "gh pr edit"),
    ("pr comment", "gh pr comment"),
    ("pr reopen", "gh pr reopen"),
    ("pr checks", "gh pr checks"),
    ("pr review", "gh pr review"),
    ("pr ready", "gh pr ready"),
    ("pr status", "gh pr status"),
    ("pr close", "gh pr close"),
    ("pr merge", "gh pr merge (blocked — policy)"),
    ("project", "gh project"),
    ("ruleset", "gh ruleset (blocked — policy)"),
    ("repo view", "gh repo view"),
)

CHROME_COMMANDS: tuple[tuple[str, str], ...] = (
    ("bookmarks ingest", "exported HTML → configured local file"),
    ("bookmarks merge", "merge new URLs from export into backup"),
    ("bookmarks snapshot", "timestamped copy under chrome.snapshots_dir"),
    ("bookmarks deploy", "validate configured local file for browser import"),
    ("photos list", "list ingested Google Photos albums"),
    ("photos ingest", "import Google Takeout zip into photos_dir"),
    ("photos status", "summarize local Google Photos inventory"),
    ("bookmarks export", "legacy alias for bookmarks ingest"),
    ("bookmarks import", "legacy alias for bookmarks deploy"),
)

TOP_LEVEL_COMMANDS: tuple[tuple[str, str], ...] = (
    ("git / g", "git shortcuts (see cli git --help)"),
    ("gh", "GitHub via gh/API — issues, labels, PRs, backlog, low-level Projects (see docs/gh.md)"),
    ("opencode", "AI entry point — chat, gh flows, raw prompts (see docs/opencode.md)"),
    ("lint", "Repository lint wrapper"),
    ("test", "Run repo test pipeline and package selection contracts"),
    ("structure", "Repository structure checks"),
    ("validate", "Data/config validation helpers"),
    ("languages", "Language inventory and metadata"),
    ("deploy", "Deploy pipeline wrapper"),
    ("release", "Release build pipeline wrapper"),
    ("restore", "restore workflows (placeholder)"),
    ("drive", "git-tags local store (iCloud) + cloud upload/download — status, ingest, deploy, sync"),
    ("chrome", "Chrome browser — bookmarks ingest, merge, snapshot, deploy"),
    ("notion", "Notion task board — pairs build / ingest / deploy / sync / cleanup"),
    ("project", "GitHub Projects — board reads, writes, pairs, recurrence"),
    ("links", "this index — docs, commands, defaults"),
    ("docker", "monitor + cleanup — stats, top, stop, delete, reset (see cli docker --help)"),
    ("contest", "Competitive programming validation harness"),
    ("configure", "Import/list configuration keys"),
    ("config", "Inspect resolved configuration"),
    ("pypi", "Build/upload/version helpers for gardusig-cli"),
    ("puzzles", "Puzzle issue helpers"),
    ("repo", "Repository inventory and hygiene helpers"),
    ("tasks", "Task pair helpers"),
    ("wiki", "Wiki repository helpers"),
)

DOCKER_QUICK_DEFAULTS: tuple[tuple[str, str], ...] = (
    ("docker ps", "running containers; --format json for agents"),
    ("docker containers", "all containers; supports --name, --status, --filter, --format json"),
    ("docker images", "images by size; supports --repository, --filter, --format json"),
    ("docker stats", "top consumers by cpu, memory, or storage"),
    ("docker top", "dashboard across cpu, memory, and storage"),
    ("docker reset", "stop all, delete containers, prune images + cache — --yes"),
    ("docker stop", "stop running containers — --yes"),
    ("docker container-delete", "remove containers — --yes"),
    ("docker image-delete", "prune unused images — --yes"),
)

DOCKER_SCRIPT_COMMANDS: tuple[tuple[str, str], ...] = ()

DOCKER_QUICK_DEFAULT_SCRIPTS: dict[str, str] = {}


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


def git_command_entries(root: Path | None = None) -> list[CatalogEntry]:
    _ = root or project_root()
    entries: list[CatalogEntry] = []
    for label, cli_cmd in GIT_COMMANDS:
        entries.append(
            CatalogEntry(
                label,
                cli=f"cli {cli_cmd}",
                doc="docs/git.md",
            )
        )
    return entries


def gh_command_entries(root: Path | None = None) -> list[CatalogEntry]:
    _ = root or project_root()
    entries: list[CatalogEntry] = []
    for label, cli_cmd in GH_COMMANDS:
        entries.append(
            CatalogEntry(
                label,
                cli=f"cli {cli_cmd}",
                doc="docs/gh.md",
            )
        )
    return entries


def chrome_command_entries(root: Path | None = None) -> list[CatalogEntry]:
    _ = root or project_root()
    entries: list[CatalogEntry] = []
    for label, note in CHROME_COMMANDS:
        entries.append(
            CatalogEntry(
                label,
                cli=f"cli chrome {label}",
                doc="docs/bookmarks.md",
                note=note,
            )
        )
    return entries
