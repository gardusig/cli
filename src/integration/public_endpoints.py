"""Canonical registry of every public cli CLI endpoint for integration checks."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

FeatureBranchMode = Literal["none", "exists", "checked_out", "merged"]

from typer.testing import CliRunner

from src import __version__
from src.cli import app
from src.integration.docker_guard import (
    cleanup_integration_temp_dir,
    integration_temp_dir,
    require_docker_integration,
)
from src.integration.git_mocks import patch_remote_git

_CLI_RUNNER = CliRunner()

CheckKind = Literal["ok", "refuse"]
REFUSE_NEEDLE = "non-interactive"
FEATURE_BRANCH = "integration-feature"


@dataclass(frozen=True)
class EndpointCheck:
    """One invocable public CLI surface."""

    label: str
    args: tuple[str, ...]
    kind: CheckKind = "ok"
    needle: str | None = None
    extra_needles: tuple[str, ...] = field(default_factory=tuple)
    needs_git: bool = False
    reset_git: bool = False
    dirty_git: bool = False
    ensure_stash: bool = False
    feature_branch: FeatureBranchMode = "none"
    ensure_second_commit: bool = False
    accept_exit_codes: tuple[int, ...] = (0,)
    extra_env: dict[str, str] = field(default_factory=dict)
    outside_git: bool = False
    failure: str | None = None


# Top-level groups (excluding hidden `g` alias — covered separately).
TOP_LEVEL_COMMANDS = (
    "links",
    "git",
    "gh",
    "opencode",
    "lint",
    "test",
    "structure",
    "validate",
    "languages",
    "deploy",
    "release",
    "restore",
    "drive",
    "notion",
    "project",
    "chrome",
    "docker",
    "contest",
    "configure",
    "config",
    "pypi",
    "pipeline",
    "puzzles",
    "repo",
    "tasks",
    "wiki",
)

# Every public `cli git …` command path (space-separated nested groups).
GIT_SUBCOMMANDS = (
    "main",
    "pull",
    "commit",
    "push",
    "start",
    "stash",
    "clean",
    "reset",
    "rebase",
    "revert",
    "tag",
    "deploy",
    "zip",
    "review",
    "docs",
    "branch list",
    "branch prune",
    "branch delete",
    "branch clear",
    "branch current",
    "branch rename",
    "diff stat",
    "diff names",
    "log oneline",
    "log messages",
    "rev parse",
    "rev-list count",
    "remote url",
    "merge-base check",
    "publish check",
    "large files",
    "post merge cleanup",
    "cherry pick",
)

# Every public `cli pypi …` command path.
PYPI_SUBCOMMANDS = (
    "build",
    "upload",
    "version check",
    "version suggest",
    "version tag-suggest",
)

_GIT_SUBCOMMAND_PATHS: frozenset[tuple[str, ...]] = frozenset(
    ("git", *sub.split()) for sub in GIT_SUBCOMMANDS
)


def endpoint_checks() -> list[EndpointCheck]:
    """All integration checks in stable order."""
    refuse = REFUSE_NEEDLE
    checks: list[EndpointCheck] = [
        EndpointCheck("root --help", ("--help",), needle="git"),
        EndpointCheck("root --version", ("--version",), needle=__version__),
        *[
            EndpointCheck(
                f"{name} missing command",
                (name, "__missing__"),
                kind="fail",
                needle="No such command",
                accept_exit_codes=(2,),
                failure="missing_command",
            )
            for name in (
                "config",
                "configure",
                "languages",
                "lint",
                "pipeline",
                "project",
                "puzzles",
                "repo",
                "structure",
                "tasks",
                "validate",
                "wiki",
            )
        ],
        EndpointCheck("drive status", ("drive", "status"), needle="Repository:"),
        EndpointCheck("restore", ("restore",), needle="not implemented yet"),
        EndpointCheck("drive help", ("drive", "--help"), needle="download"),
        EndpointCheck("notion help", ("notion", "--help"), needle="ingest"),
        EndpointCheck("project help", ("project", "--help"), needle="GitHub Projects"),
        EndpointCheck("project pairs help", ("project", "pairs", "--help"), needle="status"),
        EndpointCheck(
            "notion ingest missing token",
            ("notion", "ingest"),
            needle="NOTION_TOKEN",
            accept_exit_codes=(1,),
            failure="missing_notion_token",
        ),
        EndpointCheck("chrome help", ("chrome", "--help"), needle="merge"),
        EndpointCheck(
            "chrome bookmarks deploy missing",
            ("chrome", "bookmarks", "deploy"),
            needle="Backup not found",
            accept_exit_codes=(1,),
            extra_env={"CLI_BOOKMARKS_FILE": "/nonexistent/cli/missing-bookmarks.html"},
        ),
        EndpointCheck("gh help", ("gh", "--help"), needle="issue"),
        EndpointCheck("gh issue help", ("gh", "issue", "--help"), needle="reopen"),
        EndpointCheck("gh pr help", ("gh", "pr", "--help"), needle="checks"),
        EndpointCheck("gh project help", ("gh", "project", "--help"), needle="GitHub Projects"),
        EndpointCheck("opencode help", ("opencode", "--help"), needle="chat"),
        EndpointCheck(
            "opencode plan missing arg",
            ("opencode", "plan"),
            kind="fail",
            needle="Missing argument",
            accept_exit_codes=(2,),
            failure="missing_arg",
        ),
        EndpointCheck("lint help", ("lint", "--help"), needle="repo"),
        EndpointCheck("test help", ("test", "--help"), needle="python"),
        EndpointCheck(
            "test packages resolve",
            ("test", "packages", "resolve", "--changed-path", "src/commands/gh.py"),
            needle='"package_names"',
        ),
        EndpointCheck(
            "test packages list",
            ("test", "packages", "list", "--format", "table"),
            needle="gh:",
        ),
        EndpointCheck(
            "test packages run dry-run",
            ("test", "packages", "run", "gh", "--dry-run", "--format", "table"),
            needle="python3 -m pytest",
        ),
        EndpointCheck(
            "test packages suite",
            ("test", "packages", "suite", "--format", "table"),
            needle="packages:",
        ),
        EndpointCheck("structure help", ("structure", "--help"), needle="check"),
        EndpointCheck("validate help", ("validate", "--help"), needle="vault"),
        EndpointCheck("languages help", ("languages", "--help"), needle="show"),
        EndpointCheck("languages list", ("languages", "list"), needle="markdown"),
        EndpointCheck(
            "test java unit rejects non-java repo",
            ("test", "java", "unit"),
            kind="fail",
            accept_exit_codes=(1,),
            failure="missing_marker",
            needle="missing one of",
        ),
        EndpointCheck("deploy help", ("deploy", "--help"), needle="deploy"),
        EndpointCheck(
            "deploy refuse",
            ("deploy",),
            kind="refuse",
            needle=refuse,
            accept_exit_codes=(1,),
        ),
        EndpointCheck("release help", ("release", "--help"), needle="release"),
        EndpointCheck(
            "release build refuse",
            ("release", "build"),
            kind="refuse",
            needle=refuse,
            accept_exit_codes=(1,),
        ),
        EndpointCheck(
            "release main refuse",
            ("release", "main"),
            kind="refuse",
            needle=refuse,
            accept_exit_codes=(1,),
        ),
        EndpointCheck(
            "gh issue list",
            ("gh", "issue", "list"),
            needle='"number":',
            accept_exit_codes=(0, 1),
        ),
        EndpointCheck("links", ("links",), needle="Quick defaults"),
        EndpointCheck("docker --help", ("docker", "--help"), needle="reset"),
        EndpointCheck("docker ps help", ("docker", "ps", "--help"), needle="format"),
        EndpointCheck("docker images help", ("docker", "images", "--help"), needle="repository"),
        EndpointCheck("contest help", ("contest", "--help"), needle="validate"),
        EndpointCheck("configure help", ("configure", "--help"), needle="check"),
        EndpointCheck("config help", ("config", "--help"), needle="check"),
        EndpointCheck("pipeline help", ("pipeline", "--help"), needle="run"),
        EndpointCheck("pipeline config help", ("pipeline", "config", "--help"), needle="resolve"),
        EndpointCheck("pipeline docker help", ("pipeline", "docker", "--help"), needle="run"),
        EndpointCheck("pipeline task help", ("pipeline", "task", "--help"), needle="run"),
        EndpointCheck("puzzles help", ("puzzles", "--help"), needle="issues"),
        EndpointCheck("repo help", ("repo", "--help"), needle="inventory"),
        EndpointCheck("tasks help", ("tasks", "--help"), needle="pairs"),
        EndpointCheck("wiki help", ("wiki", "--help"), needle="repos"),
        EndpointCheck("pypi help", ("pypi", "--help"), needle="upload"),
        EndpointCheck(
            "pypi build",
            ("pypi", "build"),
            needle="Built:",
        ),
        EndpointCheck(
            "pypi build missing project",
            ("pypi", "build"),
            outside_git=True,
            needle="pyproject",
            accept_exit_codes=(1,),
            failure="missing_pyproject",
        ),
        EndpointCheck(
            "pypi upload build-only",
            ("pypi", "upload", "--yes", "--build-only"),
            needle="Built:",
        ),
        EndpointCheck(
            "pypi upload refuse",
            ("pypi", "upload"),
            kind="refuse",
            needle=refuse,
            accept_exit_codes=(1,),
        ),
        EndpointCheck(
            "pypi upload missing token",
            ("pypi", "upload", "--yes"),
            needle="PYPI_API_TOKEN",
            accept_exit_codes=(1,),
            failure="missing_pypi_token",
        ),
        EndpointCheck(
            "pypi version suggest",
            ("pypi", "version", "suggest"),
            needle="0.",
        ),
        EndpointCheck(
            "pypi version suggest missing project",
            ("pypi", "version", "suggest"),
            outside_git=True,
            needle="pyproject",
            accept_exit_codes=(1,),
            failure="missing_pyproject",
        ),
        EndpointCheck(
            "pypi version tag-suggest",
            ("pypi", "version", "tag-suggest"),
            needle="v",
        ),
        EndpointCheck(
            "pypi version tag-suggest missing project",
            ("pypi", "version", "tag-suggest"),
            outside_git=True,
            needle="pyproject",
            accept_exit_codes=(1,),
            failure="missing_pyproject",
        ),
        EndpointCheck(
            "pypi version check",
            ("pypi", "version", "check", "--base", "origin/main"),
            needle="version ok",
        ),
        EndpointCheck(
            "pypi version check not increased",
            ("pypi", "version", "check", "--base", "HEAD"),
            needle="not greater",
            accept_exit_codes=(1,),
            failure="version_not_increased",
        ),
        EndpointCheck("publish help", ("publish", "--help"), needle="deprecated"),
        EndpointCheck(
            "publish pypi build-only",
            ("publish", "pypi", "--build-only"),
            needle="Built:",
        ),
        EndpointCheck(
            "publish pypi missing token",
            ("publish", "pypi", "--yes"),
            needle="PYPI_API_TOKEN",
            accept_exit_codes=(1,),
            failure="missing_pypi_token",
        ),
        EndpointCheck(
            "git group help",
            ("git",),
            needle="start",
            accept_exit_codes=(0, 2),
        ),
        EndpointCheck("git --help", ("git", "--help"), needle="branch"),
        EndpointCheck("hidden alias g commit", ("g", "commit"), needle="nothing to commit", needs_git=True, reset_git=True),
        EndpointCheck("git docs", ("git", "docs"), needle="Documentation"),
        EndpointCheck("git large files", ("git", "large", "files", "-n", "1"), needle="src/"),
        EndpointCheck(
            "git branch current",
            ("git", "branch", "current"),
            needle="main",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git rev parse",
            ("git", "rev", "parse", "HEAD"),
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git remote url",
            ("git", "remote", "url"),
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git diff stat",
            ("git", "diff", "stat", "--base", "main", "--head", "HEAD"),
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git diff names",
            ("git", "diff", "names", "--base", "main", "--head", "HEAD"),
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git log oneline",
            ("git", "log", "oneline", "--base", "main", "--head", "HEAD"),
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git log messages",
            ("git", "log", "messages", "--base", "main", "--head", "HEAD"),
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git rev-list count",
            ("git", "rev-list", "count", "--base", "main", "--head", "HEAD"),
            needle="ahead",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git merge-base check",
            ("git", "merge-base", "check", "--base", "main", "--head", "HEAD"),
            needle="is_ancestor",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git publish check",
            ("git", "publish", "check"),
            needle="on_remote",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git review quick",
            ("git", "review", "--no-install", "--quick"),
            needle="review passed",
        ),
        EndpointCheck(
            "git commit",
            ("git", "commit"),
            needle="nothing to commit",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git branch list",
            ("git", "branch", "list"),
            needle="main",
            needs_git=True,
        ),
        EndpointCheck(
            "git stash list",
            ("git", "stash", "list"),
            needle="empty",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git stash push",
            ("git", "stash", "push"),
            needle="stashed",
            needs_git=True,
            reset_git=True,
            dirty_git=True,
        ),
        EndpointCheck(
            "git stash apply",
            ("git", "stash", "apply"),
            needle="stash applied",
            needs_git=True,
            ensure_stash=True,
        ),
        EndpointCheck(
            "git stash pop",
            ("git", "stash", "pop"),
            needle="stash popped",
            needs_git=True,
            ensure_stash=True,
        ),
        EndpointCheck(
            "git pull",
            ("git", "pull"),
            needle="pull complete",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git branch prune",
            ("git", "branch", "prune"),
            needle="pruned",
            needs_git=True,
        ),
        EndpointCheck(
            "git branch delete refuse",
            ("git", "branch", "delete", "integration-feature"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
        ),
        EndpointCheck(
            "git start explicit",
            ("git", "start", "integration-feature", "--no-prep"),
            needle="integration-feature",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git start auto",
            ("git", "start", "--no-prep"),
            needle="on branch",
            needs_git=True,
        ),
        EndpointCheck(
            "git tag local",
            ("git", "tag", "v0.0.0", "--yes"),
            needle="v0.0.0",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git tag list",
            ("git", "tag", "list"),
            needle="Local tags",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git deploy status",
            ("git", "deploy", "--status"),
            needle="deploy",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git deploy refuse",
            ("git", "deploy"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git zip",
            ("git", "zip", "v0.0.0"),
            needle=".zip",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git zip missing tag",
            ("git", "zip", "v9.9.9"),
            needle="Tag not found",
            needs_git=True,
            reset_git=True,
            accept_exit_codes=(1,),
        ),
        EndpointCheck(
            "git tag invalid format",
            ("git", "tag", "2026-06-11", "--yes"),
            needle="semver-v",
            needs_git=True,
            reset_git=True,
            accept_exit_codes=(1,),
        ),
        EndpointCheck(
            "git pull bad merge",
            ("git", "pull", "--merge", "no-such-branch-xyzzy"),
            needle="not something we can merge",
            accept_exit_codes=(1,),
            needs_git=True,
            reset_git=True,
            feature_branch="checked_out",
        ),
        EndpointCheck(
            "git commit missing path",
            ("git", "commit", "--path", "no/such/file.txt"),
            needle="did not match",
            accept_exit_codes=(1,),
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git rev-parse bad ref",
            ("git", "rev", "parse", "NOT_A_VALID_REF"),
            needle="unknown revision",
            accept_exit_codes=(1,),
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git diff stat bad base",
            ("git", "diff", "stat", "--base", "no-such-ref", "--head", "HEAD"),
            needle="unknown revision",
            accept_exit_codes=(1,),
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git diff-names bad base",
            ("git", "diff", "names", "--base", "no-such-ref", "--head", "HEAD"),
            needle="unknown revision",
            accept_exit_codes=(1,),
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git log-oneline bad base",
            ("git", "log", "oneline", "--base", "no-such-ref", "--head", "HEAD"),
            needle="unknown revision",
            accept_exit_codes=(1,),
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git log-messages bad base",
            ("git", "log", "messages", "--base", "no-such-ref", "--head", "HEAD"),
            needle="unknown revision",
            accept_exit_codes=(1,),
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git rev-list-count bad base",
            ("git", "rev-list", "count", "--base", "no-such-ref", "--head", "HEAD"),
            needle="unknown revision",
            accept_exit_codes=(1,),
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git merge-base-check outside git",
            ("git", "merge-base", "check", "--base", "main", "--head", "HEAD"),
            needle="not a git repository",
            accept_exit_codes=(1,),
            outside_git=True,
        ),
        EndpointCheck(
            "git remote-url no remote",
            ("git", "remote", "url", "no-such-remote"),
            needle="No such remote",
            accept_exit_codes=(1,),
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git branch current outside git",
            ("git", "branch", "current"),
            needle="not a git repository",
            accept_exit_codes=(1,),
            outside_git=True,
        ),
        EndpointCheck(
            "git stash apply empty",
            ("git", "stash", "apply"),
            needle="not a valid reference",
            accept_exit_codes=(1,),
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git large files outside git",
            ("git", "large", "files", "-n", "1"),
            needle="not a git repository",
            accept_exit_codes=(1,),
            outside_git=True,
        ),
        EndpointCheck(
            "git branch list outside git",
            ("git", "branch", "list"),
            needle="not a git repository",
            accept_exit_codes=(1,),
            outside_git=True,
        ),
        EndpointCheck(
            "git branch rename outside git",
            ("git", "branch", "rename", "x"),
            needle="not a git repository",
            accept_exit_codes=(1,),
            outside_git=True,
        ),
        EndpointCheck(
            "git publish check outside git",
            ("git", "publish", "check"),
            needle="not a git repository",
            accept_exit_codes=(1,),
            outside_git=True,
        ),
        EndpointCheck(
            "git branch prune outside git",
            ("git", "branch", "prune"),
            needle="not a git repository",
            accept_exit_codes=(1,),
            outside_git=True,
        ),
        EndpointCheck(
            "git review fail",
            ("git", "review", "--no-install", "--quick"),
            needle="review failed",
            accept_exit_codes=(1,),
            failure="review_fail",
        ),
        EndpointCheck(
            "git tag replace refuse",
            ("git", "tag", "v0.0.1"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git tag replace force",
            ("git", "tag", "v0.0.1", "--yes", "--force"),
            needle="v0.0.1",
            needs_git=True,
            reset_git=True,
        ),
        # Write gates — must refuse without --yes in non-interactive mode.
        EndpointCheck(
            "git push refuse main",
            ("git", "push"),
            kind="refuse",
            needle=refuse,
            extra_needles=("from_branch: main", "target_branch: wip-"),
            needs_git=True,
            reset_git=True,
            dirty_git=True,
        ),
        EndpointCheck(
            "git push refuse branch",
            ("git", "push"),
            kind="refuse",
            needle=refuse,
            extra_needles=("intent: git add -A → commit → push origin HEAD",),
            needs_git=True,
            feature_branch="checked_out",
            dirty_git=True,
        ),
        EndpointCheck("git start", ("git", "start"), kind="refuse", needle=refuse, needs_git=True),
        EndpointCheck(
            "git start push refuse",
            ("git", "start", "integration-push-branch", "--no-prep", "--push"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck("git main", ("git", "main"), kind="refuse", needle=refuse, needs_git=True),
        EndpointCheck("git clean", ("git", "clean"), kind="refuse", needle=refuse, needs_git=True),
        EndpointCheck("git reset", ("git", "reset"), kind="refuse", needle=refuse, needs_git=True),
        EndpointCheck(
            "git branch delete",
            ("git", "branch", "delete", "integration-feature"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
        ),
        EndpointCheck(
            "git branch delete merged",
            ("git", "branch", "delete", "--merged"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
        ),
        EndpointCheck(
            "git branch delete all",
            ("git", "branch", "delete", "--all"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
        ),
        EndpointCheck(
            "git branch clear",
            ("git", "branch", "clear"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
        ),
        EndpointCheck(
            "git post merge cleanup",
            ("git", "post", "merge", "cleanup"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
        ),
        EndpointCheck(
            "git stash drop",
            ("git", "stash", "drop"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
        ),
        EndpointCheck(
            "git stash clear",
            ("git", "stash", "clear"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
        ),
        EndpointCheck("git rebase", ("git", "rebase"), kind="refuse", needle=refuse, needs_git=True),
        EndpointCheck(
            "git revert",
            ("git", "revert", "HEAD"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
        ),
        EndpointCheck(
            "git cherry pick",
            ("git", "cherry", "pick", "HEAD"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
        ),
        EndpointCheck(
            "git tag push refuse",
            ("git", "tag", "push", "v0.0.2"),
            kind="refuse",
            needle=refuse,
            needs_git=True,
            reset_git=True,
        ),
        # Gated writes with --yes (remote fetch/push/ls-remote mocked in run_all_endpoint_checks).
        EndpointCheck(
            "git push yes from main",
            ("git", "push", "--yes"),
            needle="pushed",
            extra_needles=("from_branch: main", "target_branch: wip-"),
            needs_git=True,
            reset_git=True,
            dirty_git=True,
        ),
        EndpointCheck(
            "git push yes from branch",
            ("git", "push", "--yes"),
            needle="pushed",
            extra_needles=("intent: git add -A → commit → push origin HEAD",),
            needs_git=True,
            reset_git=True,
            feature_branch="checked_out",
            dirty_git=True,
        ),
        EndpointCheck(
            "git clean yes",
            ("git", "clean", "--yes"),
            needle="artifacts removed",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git reset main-only yes",
            ("git", "reset", "--yes", "--main-only"),
            needle="reset",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git start yes",
            ("git", "start", "integration-start", "--yes"),
            needle="started",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git reset yes",
            ("git", "reset", "--yes"),
            needle="synced with remote",
            needs_git=True,
            reset_git=True,
            feature_branch="merged",
        ),
        EndpointCheck(
            "git reset delete-merged yes",
            ("git", "reset", "--yes", "--delete-merged"),
            needle="removed",
            needs_git=True,
            reset_git=True,
            feature_branch="merged",
        ),
        EndpointCheck(
            "git reset all-local yes",
            ("git", "reset", "--yes", "--all-local"),
            needle="reset",
            needs_git=True,
            reset_git=True,
            feature_branch="exists",
        ),
        EndpointCheck(
            "git reset discard yes",
            ("git", "reset", "--yes", "--discard"),
            needle="reset",
            needs_git=True,
            reset_git=True,
            feature_branch="checked_out",
            dirty_git=True,
        ),
        EndpointCheck(
            "git main yes",
            ("git", "main", "--yes"),
            needle="main aligned",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git branch delete yes",
            ("git", "branch", "delete", "integration-feature", "--yes", "--no-remote"),
            needle="deleted",
            needs_git=True,
            reset_git=True,
            feature_branch="exists",
        ),
        EndpointCheck(
            "git branch delete yes",
            ("git", "branch", "delete", "integration-feature", "--yes", "--no-remote"),
            needle="deleted",
            needs_git=True,
            reset_git=True,
            feature_branch="exists",
        ),
        EndpointCheck(
            "git branch rename",
            ("git", "branch", "rename", "integration-renamed"),
            needle="renamed",
            needs_git=True,
            reset_git=True,
            feature_branch="checked_out",
        ),
        EndpointCheck(
            "git stash drop yes",
            ("git", "stash", "drop", "--yes"),
            needle="stash dropped",
            needs_git=True,
            ensure_stash=True,
        ),
        EndpointCheck(
            "git stash clear yes",
            ("git", "stash", "clear", "--yes"),
            needle="stash cleared",
            needs_git=True,
            ensure_stash=True,
        ),
        EndpointCheck(
            "git rebase yes",
            ("git", "rebase", "--yes"),
            needle="rebase step complete",
            needs_git=True,
            reset_git=True,
            feature_branch="checked_out",
        ),
        EndpointCheck(
            "git revert yes",
            ("git", "revert", "HEAD", "--yes"),
            needle="revert step complete",
            needs_git=True,
            reset_git=True,
            ensure_second_commit=True,
        ),
        EndpointCheck(
            "git cherry pick yes",
            ("git", "cherry", "pick", FEATURE_BRANCH, "--yes"),
            needle="cherry-pick step complete",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git tag push yes",
            ("git", "tag", "push", "v0.0.3", "--yes"),
            needle="v0.0.3",
            needs_git=True,
            reset_git=True,
        ),
        EndpointCheck(
            "git branch delete merged yes",
            ("git", "branch", "delete", "--merged", "--yes"),
            needle="deleted",
            needs_git=True,
            reset_git=True,
            feature_branch="merged",
        ),
        EndpointCheck(
            "git branch delete all yes",
            ("git", "branch", "delete", "--all", "--yes"),
            needle="deleted",
            needs_git=True,
            reset_git=True,
            feature_branch="exists",
        ),
        EndpointCheck(
            "git branch clear yes",
            ("git", "branch", "clear", "--yes"),
            needle="cleared",
            needs_git=True,
            reset_git=True,
            feature_branch="exists",
        ),
        EndpointCheck(
            "git post merge cleanup yes",
            ("git", "post", "merge", "cleanup", "--yes"),
            needle="cleanup done",
            needs_git=True,
            reset_git=True,
            feature_branch="merged",
        ),
        EndpointCheck(
            "git start push yes",
            ("git", "start", "integration-push-branch", "--no-prep", "--push", "--yes"),
            needle="integration-push-branch",
            needs_git=True,
            reset_git=True,
        ),
    ]
    return checks


def _collect_typer_command_paths(typer_instance, prefix: tuple[str, ...] = ()) -> set[str]:
    paths: set[str] = set()
    for group in typer_instance.registered_groups:
        if group.name:
            paths |= _collect_typer_command_paths(group.typer_instance, prefix + (group.name,))
    for cmd in typer_instance.registered_commands:
        if cmd.name:
            paths.add(" ".join(prefix + (cmd.name,)))
    return paths


def _pypi_command_path_from_check_args(args: tuple[str, ...]) -> str | None:
    if not args or args[0] != "pypi":
        return None
    rest = [a for a in args[1:] if not a.startswith("-")]
    if len(rest) >= 2 and rest[0] == "version":
        candidate = f"version {rest[1]}"
        if candidate in PYPI_SUBCOMMANDS:
            return candidate
    if rest:
        candidate = rest[0]
        if candidate in PYPI_SUBCOMMANDS:
            return candidate
    return None


def _git_command_path_from_check_args(args: tuple[str, ...]) -> str | None:
    if not args or args[0] != "git":
        return None
    rest = [a for a in args[1:] if not a.startswith("-")]
    for length in range(len(rest), 0, -1):
        candidate = " ".join(rest[:length])
        if candidate in GIT_SUBCOMMANDS:
            return candidate
    return None


def registered_git_subcommands() -> set[str]:
    for group in app.registered_groups:
        if group.name in {"git", "g"}:
            return _collect_typer_command_paths(group.typer_instance)
    return set()


def assert_registry_covers_git_commands() -> None:
    registered = registered_git_subcommands()
    expected = set(GIT_SUBCOMMANDS)
    missing = expected - registered
    extra = registered - expected
    if missing or extra:
        raise AssertionError(f"git registry drift: missing={sorted(missing)} extra={sorted(extra)}")


def _git_env() -> dict[str, str]:
    """Subprocess env without inherited GIT_DIR / GIT_WORK_TREE bleed."""
    env = os.environ.copy()
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    return env


def ensure_project_git(repo_root: Path) -> None:
    """Init repo_root when copied without .git (Docker integration workspace)."""
    if (repo_root / ".git").exists():
        return
    env = _git_env()
    git = ["git", "-C", str(repo_root)]
    subprocess.run(
        ["git", "config", "--global", "--add", "safe.directory", str(repo_root.resolve())],
        check=True,
        env=env,
    )
    subprocess.run([*git, "init", "-b", "main"], check=True, capture_output=True, env=env)
    subprocess.run([*git, "config", "user.email", "cli@example.test"], check=True, env=env)
    subprocess.run([*git, "config", "user.name", "Cli Test"], check=True, env=env)
    subprocess.run([*git, "add", "-A"], check=True, capture_output=True, env=env)
    subprocess.run(
        [*git, "commit", "-m", "integration snapshot"],
        check=True,
        capture_output=True,
        env=env,
    )


def prepare_git_repo(path: Path) -> None:
    """Disposable repo with local origin remote for CLI_GIT_ROOT checks."""
    path.mkdir(parents=True, exist_ok=True)
    bare = path.parent / f"{path.name}-origin.git"
    if bare.exists():
        shutil.rmtree(bare)
    subprocess.run(["git", "init", "--bare", "-b", "main", str(bare)], check=True, capture_output=True)
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(path), "config", "user.email", "cli@example.test"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "config", "user.name", "Cli Integration"],
        check=True,
    )
    readme = path / "README.md"
    readme.write_text("integration\n", encoding="utf-8")
    pyproject = path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "integration"\nversion = "0.0.0"\n', encoding="utf-8")
    src_dir = path / "src"
    src_dir.mkdir(exist_ok=True)
    (src_dir / "__init__.py").write_text('__version__ = "0.0.0"\n', encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "README.md", "pyproject.toml", "src/__init__.py"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(path), "commit", "-m", "initial"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "remote", "add", "origin", str(bare)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "push", "-u", "origin", "main"],
        check=True,
        capture_output=True,
    )


def dirty_integration_git(git_root: Path) -> None:
    """Uncommitted change so stash push creates an entry."""
    readme = git_root / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "\n", encoding="utf-8")


def setup_feature_branch(git_root: Path, mode: FeatureBranchMode) -> None:
    """Prepare integration-feature branch for destructive CLI checks."""
    if mode == "none":
        return
    git = ["git", "-C", str(git_root)]
    subprocess.run([*git, "checkout", "-b", FEATURE_BRANCH], check=True, capture_output=True)
    if mode == "merged":
        subprocess.run([*git, "commit", "--allow-empty", "-m", "feature"], check=True, capture_output=True)
        subprocess.run([*git, "checkout", "main"], check=True, capture_output=True)
        subprocess.run([*git, "merge", FEATURE_BRANCH, "--no-edit"], check=True, capture_output=True)
    elif mode == "exists":
        subprocess.run([*git, "checkout", "main"], check=True, capture_output=True)
    # checked_out: stay on FEATURE_BRANCH


def add_second_commit(git_root: Path, *, on_feature: bool = False) -> None:
    """Add a commit on main (or current branch) for revert/cherry-pick checks."""
    git = ["git", "-C", str(git_root)]
    if not on_feature:
        subprocess.run([*git, "checkout", "main"], check=False, capture_output=True)
    marker = git_root / ("feature-marker.txt" if on_feature else "second-commit.txt")
    marker.write_text("marker\n", encoding="utf-8")
    subprocess.run([*git, "add", marker.name], check=True, capture_output=True)
    subprocess.run([*git, "commit", "-m", "second"], check=True, capture_output=True)


def setup_cherry_pick(git_root: Path) -> None:
    """Feature branch with unique commit, then checkout main for cherry-pick."""
    setup_feature_branch(git_root, "checked_out")
    add_second_commit(git_root, on_feature=True)
    subprocess.run(
        ["git", "-C", str(git_root), "checkout", "main"],
        check=True,
        capture_output=True,
    )


def reset_integration_git(git_root: Path) -> None:
    """Return disposable repo to clean synced main (upstream/fork/origin tip)."""
    from src.services.git_shortcuts import GitShortcuts

    git = ["git", "-C", str(git_root)]
    subprocess.run([*git, "checkout", "main"], check=False, capture_output=True)
    subprocess.run([*git, "reset", "--hard"], check=True, capture_output=True)
    subprocess.run([*git, "clean", "-fd"], check=True, capture_output=True)
    subprocess.run([*git, "stash", "clear"], check=False, capture_output=True)
    tags = subprocess.run([*git, "tag", "-l"], capture_output=True, text=True, check=False)
    for line in tags.stdout.splitlines():
        name = line.strip()
        if name:
            subprocess.run([*git, "tag", "-d", name], check=False, capture_output=True)
    result = subprocess.run(
        [*git, "branch", "--format=%(refname:short)"],
        capture_output=True,
        text=True,
        check=True,
    )
    for line in result.stdout.splitlines():
        name = line.strip()
        if name and name != "main":
            subprocess.run([*git, "branch", "-D", name], check=False, capture_output=True)
    GitShortcuts(top=str(git_root)).sync_main(yes=True, keep_ignored=False)


def git_subcommands_covered_by_checks() -> set[str]:
    covered: set[str] = set()
    for check in endpoint_checks():
        path = _git_command_path_from_check_args(check.args)
        if path:
            covered.add(path)
    return covered


def assert_every_git_subcommand_checked() -> None:
    missing = set(GIT_SUBCOMMANDS) - git_subcommands_covered_by_checks()
    if missing:
        raise AssertionError(f"integration checks missing git subcommands: {sorted(missing)}")


def pypi_subcommands_with_ok_check() -> set[str]:
    ok: set[str] = set()
    for check in endpoint_checks():
        if not _endpoint_check_is_success(check):
            continue
        path = _pypi_command_path_from_check_args(check.args)
        if path:
            ok.add(path)
    return ok


def pypi_subcommands_with_failure_check() -> set[str]:
    failed: set[str] = set()
    for check in endpoint_checks():
        if not _endpoint_check_is_failure(check):
            continue
        path = _pypi_command_path_from_check_args(check.args)
        if path:
            failed.add(path)
    return failed


def assert_every_pypi_subcommand_has_ok_and_failure_check() -> None:
    missing_ok = set(PYPI_SUBCOMMANDS) - pypi_subcommands_with_ok_check()
    missing_fail = set(PYPI_SUBCOMMANDS) - pypi_subcommands_with_failure_check()
    if missing_ok:
        raise AssertionError(f"pypi subcommands without ok integration check: {sorted(missing_ok)}")
    if missing_fail:
        raise AssertionError(
            f"pypi subcommands without failure integration check: {sorted(missing_fail)}"
        )


def git_subcommands_with_ok_check() -> set[str]:
    ok: set[str] = set()
    for check in endpoint_checks():
        if not _endpoint_check_is_success(check):
            continue
        path = _git_command_path_from_check_args(check.args)
        if path:
            ok.add(path)
    return ok


def _endpoint_check_is_success(check: EndpointCheck) -> bool:
    return check.kind == "ok" and 0 in check.accept_exit_codes


def _endpoint_check_is_failure(check: EndpointCheck) -> bool:
    return check.kind == "refuse" or check.failure is not None or (
        check.kind == "ok" and 0 not in check.accept_exit_codes
    )


def git_subcommands_with_failure_check() -> set[str]:
    failed: set[str] = set()
    for check in endpoint_checks():
        if not _endpoint_check_is_failure(check):
            continue
        path = _git_command_path_from_check_args(check.args)
        if path:
            failed.add(path)
    return failed


_GIT_SUBCOMMANDS_FAIL_EXEMPT = frozenset({"docs"})


def assert_every_git_subcommand_has_ok_check() -> None:
    """Every public git subcommand must have at least one successful integration path."""
    missing = set(GIT_SUBCOMMANDS) - git_subcommands_with_ok_check()
    if missing:
        raise AssertionError(f"git subcommands without ok integration check: {sorted(missing)}")


def assert_every_git_subcommand_has_failure_check() -> None:
    """Every public git subcommand must have at least one failure/refusal integration path."""
    missing = (
        set(GIT_SUBCOMMANDS) - git_subcommands_with_failure_check() - _GIT_SUBCOMMANDS_FAIL_EXEMPT
    )
    if missing:
        raise AssertionError(f"git subcommands without failure integration check: {sorted(missing)}")


def assert_every_git_subcommand_has_ok_and_failure_check() -> None:
    assert_every_git_subcommand_has_ok_check()
    assert_every_git_subcommand_has_failure_check()


def assert_every_top_level_command_checked() -> None:
    for name in TOP_LEVEL_COMMANDS:
        if name in {"git", "pypi"}:
            if name == "git" and not any(c.label == "git group help" for c in endpoint_checks()):
                raise AssertionError("missing integration check for git group help")
            if name == "pypi" and not any(c.label == "pypi help" for c in endpoint_checks()):
                raise AssertionError("missing integration check for pypi help")
            continue
        if not any(c.args and c.args[0] == name for c in endpoint_checks()):
            raise AssertionError(f"missing integration check for top-level command: {name}")


def ensure_stash_entry(repo_root: Path, git_root: Path) -> tuple[int, str]:
    """Reset, dirty tree, and stash push so apply/pop have an entry."""
    reset_integration_git(git_root)
    dirty_integration_git(git_root)
    return run_endpoint_check(
        EndpointCheck("stash setup", ("git", "stash", "push"), needs_git=True),
        repo_root=repo_root,
        git_root=git_root,
    )


def run_endpoint_check(
    check: EndpointCheck,
    *,
    repo_root: Path,
    git_root: Path | None,
    outside_git_root: Path | None = None,
) -> tuple[int, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    if check.outside_git and outside_git_root is not None:
        env.pop("CLI_GIT_ROOT", None)
        cwd = outside_git_root
    elif check.needs_git and git_root is not None:
        env["CLI_GIT_ROOT"] = str(git_root)
        cwd = repo_root
    else:
        # Block CLI_GIT_ROOT bleed from Docker CI (whole-pytest env var).
        env.pop("CLI_GIT_ROOT", None)
        cwd = repo_root
    from contextlib import nullcontext
    from unittest.mock import patch

    env.update(check.extra_env)
    token_patch = nullcontext()
    if check.failure == "missing_notion_token":
        env.pop("NOTION_TOKEN", None)
        token_patch = patch(
            "src.commands.notion.require_notion_token",
            side_effect=RuntimeError("NOTION_TOKEN is not set"),
        )
    if check.failure == "missing_pypi_token":
        env.pop("PYPI_API_TOKEN", None)
    project_patch = nullcontext()
    version_patch = nullcontext()
    if check.failure == "missing_pyproject" and outside_git_root is not None:
        project_patch = patch("src.commands.pypi.project_root", return_value=outside_git_root)
    if check.label == "pypi version check":
        version_patch = patch(
            "src.commands.pypi.assert_version_increased_vs_ref",
            return_value="0.1.1",
        )
    with _push_cwd(cwd), token_patch, project_patch, version_patch:
        result = _CLI_RUNNER.invoke(app, list(check.args), env=env)
    output = result.stdout + (result.stderr or "")
    if result.exception is not None:
        output += f"\n{result.exception}"
    return result.exit_code, output


class _push_cwd:
    """Temporarily chdir for git commands that resolve repo root from cwd."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.previous = Path.cwd()

    def __enter__(self) -> None:
        os.chdir(self.path)

    def __exit__(self, *args: object) -> None:
        os.chdir(self.previous)


def execute_endpoint_integration_check(
    check: EndpointCheck,
    *,
    repo_root: Path,
    git_root: Path | None,
    outside_git_root: Path,
) -> list[str]:
    """Run one endpoint check with the same setup as run_all_endpoint_checks."""
    from contextlib import nullcontext
    from unittest.mock import patch

    errors: list[str] = []
    if check.reset_git and git_root is not None:
        reset_integration_git(git_root)
    if check.label == "git tag replace refuse" and git_root is not None:
        subprocess.run(
            ["git", "-C", str(git_root), "tag", "-a", "v0.0.1", "-m", "v0.0.1"],
            check=True,
            capture_output=True,
        )
    if check.label == "git tag replace force" and git_root is not None:
        subprocess.run(
            ["git", "-C", str(git_root), "tag", "-a", "v0.0.1", "-m", "v0.0.1"],
            check=True,
            capture_output=True,
        )
    if check.label in {"git tag push yes", "git tag push refuse"} and git_root is not None:
        tag_name = "v0.0.3" if check.label == "git tag push yes" else "v0.0.2"
        subprocess.run(
            ["git", "-C", str(git_root), "tag", "-a", tag_name, "-m", tag_name],
            check=True,
            capture_output=True,
        )
    if check.label == "git zip" and git_root is not None:
        subprocess.run(
            ["git", "-C", str(git_root), "tag", "-a", "v0.0.0", "-m", "v0.0.0"],
            check=True,
            capture_output=True,
        )
    if check.label == "git cherry pick yes" and git_root is not None:
        setup_cherry_pick(git_root)
    elif git_root is not None and check.feature_branch != "none":
        setup_feature_branch(git_root, check.feature_branch)
    elif check.ensure_second_commit and git_root is not None:
        add_second_commit(git_root, on_feature=False)
    if check.dirty_git and git_root is not None:
        dirty_integration_git(git_root)
    if check.ensure_stash and git_root is not None:
        setup_code, setup_out = ensure_stash_entry(repo_root, git_root)
        if setup_code != 0:
            return [f"{check.label} setup: stash push failed ({setup_code})\n{setup_out}"]
    if check.label == "gh issue list" and shutil.which("gh") is None:
        return []
    review_patch = nullcontext()
    if check.failure == "review_fail":
        review_patch = patch("src.commands.git.run_review", return_value=1)
    deploy_patch = nullcontext()
    if check.label in {"git deploy status", "git deploy refuse"}:
        from src.services.git_deploy import DeployAssessment

        deploy_patch = patch(
            "src.commands.git.assess_deploy_readiness",
            return_value=DeployAssessment(
                repo="integration",
                main_sha="a" * 40,
                latest_tag=None,
                tag_sha=None,
                needs_tag=True,
                suggested_tag="v0.0.1",
                open_prs=(),
            ),
        )
    with review_patch, deploy_patch:
        code, output = run_endpoint_check(
            check,
            repo_root=repo_root,
            git_root=git_root,
            outside_git_root=outside_git_root,
        )
    if check.kind == "ok":
        if code not in check.accept_exit_codes:
            errors.append(
                f"{check.label}: expected exit {check.accept_exit_codes}, got {code}\n{output}"
            )
            return errors
    else:
        if code == 0:
            errors.append(f"{check.label}: expected refusal, got exit 0\n{output}")
            return errors
    for needle in (check.needle, *check.extra_needles):
        if needle and needle not in output:
            errors.append(f"{check.label}: missing needle {needle!r}\n{output}")
    if check.reset_git and git_root is not None:
        reset_integration_git(git_root)
    return errors


def run_all_endpoint_checks(repo_root: Path, git_root: Path | None = None) -> list[str]:
    """Run every check; return error messages (empty if all passed)."""
    from contextlib import nullcontext
    from unittest.mock import patch

    require_docker_integration(context="run_all_endpoint_checks")
    ensure_project_git(repo_root)
    assert_registry_covers_git_commands()
    assert_every_git_subcommand_checked()
    assert_every_git_subcommand_has_ok_and_failure_check()
    assert_every_pypi_subcommand_has_ok_and_failure_check()
    assert_every_top_level_command_checked()
    outside_git_root = integration_temp_dir("cli-outside-git-")
    errors: list[str] = []
    try:
        with patch_remote_git():
            for check in endpoint_checks():
                errors.extend(
                    execute_endpoint_integration_check(
                        check,
                        repo_root=repo_root,
                        git_root=git_root,
                        outside_git_root=outside_git_root,
                    )
                )
    finally:
        cleanup_integration_temp_dir(outside_git_root)
    return errors
