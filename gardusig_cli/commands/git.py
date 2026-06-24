from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich import print as rprint

from gardusig_cli.internal.read.git import git_worktree_snapshot
from gardusig_cli.internal.write.gate import WRITE_GATE_DELIMITER, require_write_gate
from gardusig_cli.services.backup_zip import archive_tag_zip
from gardusig_cli.services.git_review import run_review
from gardusig_cli.services.git_shortcuts import GitShortcuts
from gardusig_cli.utils.config import (
    default_zip_path,
    project_root,
    repo_encrypt_backup,
    require_backup_zip_password,
    tag_zip_basename,
)
from gardusig_cli.utils.quick_defaults import default_tag_name, suggest_branch_name

git_app = typer.Typer(help="Git shortcuts (commit message defaults to '.').", no_args_is_help=True)

branch_app = typer.Typer(help="Branch hygiene.", no_args_is_help=True)
diff_app = typer.Typer(help="Read-only diffs.", no_args_is_help=True)
log_app = typer.Typer(help="Read-only history.", no_args_is_help=True)
rev_app = typer.Typer(help="Read-only ref resolution.", no_args_is_help=True)
rev_list_app = typer.Typer(help="Read-only revision lists.", no_args_is_help=True)
remote_app = typer.Typer(help="Read-only remotes.", no_args_is_help=True)
merge_base_app = typer.Typer(help="Read-only merge-base checks.", no_args_is_help=True)
git_publish_app = typer.Typer(help="Read-only publish checks.", no_args_is_help=True)
large_app = typer.Typer(help="Large file inventory.", no_args_is_help=True)
post_app = typer.Typer(help="Post-merge workflows.", no_args_is_help=True)
post_merge_app = typer.Typer(help="After merge.", no_args_is_help=True)
cherry_app = typer.Typer(help="Cherry-pick.", no_args_is_help=True)


def _svc() -> GitShortcuts:
    return GitShortcuts()


def _branch_preview_lines(
    label: str,
    branches: list[str],
    *,
    prefix: str = "",
    limit: int = 20,
) -> list[str]:
    lines = [f"{label}: {len(branches)}"]
    for name in branches[:limit]:
        lines.append(f"  - {prefix}{name}")
    if len(branches) > limit:
        lines.append(f"  ... ({len(branches) - limit} more)")
    return lines


def _write_gate(
    operation: str,
    *,
    yes: bool = False,
    question: str | None = None,
    extra_lines: list[str] | None = None,
) -> None:
    """Read worktree snapshot, show delimiter, then Q&A before write."""
    snapshot = git_worktree_snapshot(_svc())
    require_write_gate(
        operation,
        snapshot.summary_lines(),
        question=question,
        yes=yes,
        extra_lines=extra_lines,
    )


@git_app.command("main")
def main_cmd(
    yes: bool = typer.Option(False, "--yes", "-y", help="Discard dirty tree and align."),
    keep_ignored: bool = typer.Option(False, "--keep-ignored", help="Use git clean -fd instead of -fdx."),
) -> None:
    """Align local main to canonical remote main."""
    _write_gate("main", yes=yes, question="Reset main to remote and clean working tree?")
    _svc().align_main(yes=True, keep_ignored=keep_ignored)
    rprint("[green]main aligned[/green]")


@git_app.command("pull")
def pull_cmd(
    merge_branch: str | None = typer.Option(None, "--merge", help="Named branch/ref to merge into current."),
) -> None:
    """Fetch and merge upstream + canonical main."""
    _svc().pull(merge_branch=merge_branch)
    rprint("[green]pull complete[/green]")


@git_app.command("commit")
def commit_cmd(
    message: str = typer.Option(".", "-m", "--message", help="Commit subject."),
    path: list[str] = typer.Option(None, "--path", help="Stage only these paths (repeatable)."),
) -> None:
    """Stage and commit (no-op if clean)."""
    created = _svc().commit(message, paths=path)
    if created:
        rprint(f"[green]committed[/green] ({message!r})")
    else:
        rprint("[yellow]nothing to commit[/yellow]")


def _push_plan(
    svc: GitShortcuts,
    message: str,
    *,
    allow_main: bool,
) -> tuple[str, list[str]]:
    """Write-gate question + intent lines for push (start first when on main)."""
    current = svc.current_branch()
    remote = "origin" if svc.remote_exists("origin") else "(none)"
    dirty = svc.is_dirty()
    if current == "main" and not allow_main:
        new_branch = suggest_branch_name(svc.local_branch_names(exclude_main=False))
        question = f"Start {new_branch!r}, commit, and push to {remote}?"
        lines = [
            f"intent: start {new_branch!r} (no prep) → add → commit → push",
            "from_branch: main",
            f"target_branch: {new_branch}",
            f"commit_message: {message!r}",
            f"dirty: {dirty}",
            f"remote: {remote}",
        ]
        return question, lines

    question = f"Commit and push {current!r} to {remote}?"
    lines = [
        "intent: git add -A → commit → push origin HEAD",
        f"branch: {current}",
        f"commit_message: {message!r}",
        f"dirty: {dirty}",
        f"remote: {remote}",
    ]
    if current == "main" and allow_main:
        lines.append("note: pushing directly on main (--allow-main)")
    return question, lines


@git_app.command("push")
def push_cmd(
    allow_main: bool = typer.Option(False, "--allow-main", help="Allow pushing from main."),
    message: str = typer.Option(".", "-m", "--message", help="Commit message if tree is dirty."),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt; stage, commit, and push.",
    ),
) -> None:
    """Stage if dirty, commit, and push (start first when on main)."""
    svc = _svc()
    question, intent_lines = _push_plan(svc, message, allow_main=allow_main)
    _write_gate("push", yes=yes, question=question, extra_lines=intent_lines)
    branch = svc.push(allow_main=allow_main, message=message, yes=True)
    rprint(f"[green]pushed[/green] on {branch}")


def _align_main_intent_lines(svc: GitShortcuts, *, keep_ignored: bool) -> list[str]:
    clean_mode = "git clean -fd" if keep_ignored else "git clean -fdx"
    return [
        f"intent: checkout main → fetch → reset --hard {svc.best_main_ref()} → " + clean_mode,
        f"canonical_main: {svc.canonical_main_ref()}",
        f"best_main: {svc.best_main_ref()}",
        f"dirty: {svc.is_dirty()}",
    ]


def _reset_main_intent_lines(
    svc: GitShortcuts,
    message: str,
    *,
    keep_ignored: bool,
    discard: bool,
) -> list[str]:
    lines = _align_main_intent_lines(svc, keep_ignored=keep_ignored)
    current = svc.current_branch()
    if current != "main" and svc.is_dirty():
        if discard:
            lines.append("leave_branch: discard uncommitted changes")
        else:
            lines.append(f"leave_branch: commit with message {message!r}")
    return lines


def _reset_branch_intent_lines(
    svc: GitShortcuts,
    *,
    all_local: bool,
) -> list[str]:
    if all_local:
        branches = svc.local_branch_names(exclude_main=True)
        return [
            "delete_mode: all local branches except main",
            *_branch_preview_lines("local_branches_to_delete", branches),
        ]
    branches = svc.merged_branch_names(include_current=True)
    remote_only = svc.merged_remote_branch_names()
    return [
        "delete_mode: merged branches only (local + remote)",
        *_branch_preview_lines("merged_local_branches", branches),
        *_branch_preview_lines("merged_remote_branches", remote_only, prefix="origin/"),
    ]



@git_app.command("clean")
def clean_cmd(
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm removing build/test artifacts."),
    keep_ignored: bool = typer.Option(False, "--keep-ignored", help="Use git clean -fd instead of -fdx."),
) -> None:
    """Remove local build/test artifacts (dist, coverage, integration scratch) via git clean."""
    mode = "git clean -fd" if keep_ignored else "git clean -fdx (excludes .venv)"
    _write_gate(
        "clean",
        yes=yes,
        question="Remove local build and test artifacts?",
        extra_lines=[f"intent: {mode}"],
    )
    _svc().clean_worktree(keep_ignored=keep_ignored)
    rprint("[green]clean[/green] — artifacts removed")


@git_app.command("reset")
def reset_cmd(
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm return to synced main."),
    keep_ignored: bool = typer.Option(False, "--keep-ignored", help="Use git clean -fd instead of -fdx."),
    main_only: bool = typer.Option(
        False,
        "--main-only",
        help="Sync main only; do not offer branch cleanup.",
    ),
    delete_merged: bool = typer.Option(
        False,
        "--delete-merged",
        help="After sync, delete merged branches (non-interactive with --yes).",
    ),
    all_local: bool = typer.Option(
        False,
        "--all-local",
        help="After sync, delete every local branch except main (requires --yes).",
    ),
    message: str = typer.Option(
        ".",
        "-m",
        "--message",
        help="Commit message when leaving a dirty branch (default: commit with '.').",
    ),
    discard: bool = typer.Option(
        False,
        "--discard",
        help="Discard uncommitted changes on the current branch instead of committing.",
    ),
) -> None:
    """Checkout main, sync with remote (fetch + pull), then optionally delete merged branches."""
    svc = _svc()
    _write_gate(
        "reset",
        yes=yes,
        question="Checkout main, sync with remote, and clean working tree?",
        extra_lines=_reset_main_intent_lines(
            svc,
            message,
            keep_ignored=keep_ignored,
            discard=discard,
        ),
    )
    svc.reset(
        yes=True,
        keep_ignored=keep_ignored,
        main_only=True,
        branch_message=message,
        discard=discard,
    )
    rprint("[green]reset[/green] — on main, synced with remote")

    if main_only:
        return

    if all_local:
        preview = svc.local_branch_names(exclude_main=True)
        operation = "reset-all-local"
        question = "Delete ALL local branches except main?"
    else:
        local_merged = svc.merged_branch_names(include_current=True)
        remote_merged = svc.merged_remote_branch_names()
        preview = local_merged or remote_merged
        operation = "reset-delete-merged"
        question = "Delete all merged branches? (cli git branch delete --merged)"

    if not preview:
        return

    if all_local:
        if not yes:
            raise typer.Exit("Pass --yes with --all-local in non-interactive mode.")
        gate_yes = True
    elif delete_merged and yes:
        gate_yes = True
    elif sys.stdin.isatty():
        gate_yes = False
    else:
        return

    _write_gate(
        operation,
        yes=gate_yes,
        question=question,
        extra_lines=_reset_branch_intent_lines(svc, all_local=all_local),
    )

    if all_local:
        deleted = svc.delete_all_local_branches(yes=True)
    else:
        deleted = svc.branch_delete_all_merged(yes=True)

    if deleted:
        rprint(f"[green]reset[/green] — removed {len(deleted)} branch(es)")


@git_app.command("start")
def start_cmd(
    branch: str | None = typer.Argument(
        None,
        help="Branch name (default wip-YYMMDD-NNN; use issue slug e.g. issue-9-docker).",
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm align main + new branch (or push)."),
    keep_ignored: bool = typer.Option(False, "--keep-ignored", help="Use git clean -fd instead of -fdx."),
    no_prep: bool = typer.Option(
        False,
        "--no-prep",
        help="Branch from current HEAD without aligning main.",
    ),
    no_push: bool = typer.Option(True, "--no-push/--push", help="Push new branch after create."),
) -> None:
    """Start issue work: sync main, then create a feature branch."""
    svc = _svc()
    branch_name = branch or suggest_branch_name(svc.local_branch_names(exclude_main=False))
    if not no_prep:
        extra = [
            "intent: align main → git checkout -b",
            f"branch_to_create: {branch_name}",
            *_align_main_intent_lines(svc, keep_ignored=keep_ignored),
        ]
        _write_gate(
            "start",
            yes=yes,
            question=f"Sync main and start branch {branch_name!r}?",
            extra_lines=extra,
        )
    elif not no_push:
        _write_gate("start-push", yes=yes, question="Push new branch to remote?")
    name = svc.start(
        branch_name,
        yes=yes,
        keep_ignored=keep_ignored,
        prep=not no_prep,
        no_push=no_push,
    )
    if no_prep:
        rprint(f"[green]on branch[/green] {name}")
    else:
        rprint(f"[green]started[/green] on branch {name}")


@git_app.command("stash")
def stash_cmd(
    action: str = typer.Argument("list", help="push|list|apply|pop|drop|clear"),
    message: str | None = typer.Option(None, "-m", "--message"),
    index: int = typer.Option(0, "--index", help="Stash index for apply/pop/drop."),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Stash operations."""
    svc = _svc()
    if action == "push":
        svc.stash_push(message)
        rprint("[green]stashed[/green]")
    elif action == "list":
        rprint(svc.stash_list() or "(empty)")
    elif action == "apply":
        svc.stash_apply(index)
        rprint("[green]stash applied[/green]")
    elif action == "pop":
        svc.stash_pop(index)
        rprint("[green]stash popped[/green]")
    elif action == "drop":
        _write_gate("stash-drop", yes=yes, question="Drop stash entry?")
        svc.stash_drop(index, yes=True)
        rprint("[green]stash dropped[/green]")
    elif action == "clear":
        _write_gate("stash-clear", yes=yes, question="Clear all stashes?")
        svc.stash_clear(yes=True)
        rprint("[green]stash cleared[/green]")
    else:
        raise typer.BadParameter(f"Unknown stash action: {action}")


@branch_app.command("list")
def branch_list_cmd() -> None:
    """List local branches."""
    rprint(_svc().branch_list())


@branch_app.command("prune")
def branch_prune_cmd() -> None:
    """Prune stale remote-tracking branches."""
    _svc().branch_prune()
    rprint("[green]pruned[/green]")


def _branch_delete_merged_intent_lines(svc: GitShortcuts) -> list[str]:
    local = svc.merged_branch_names(include_current=True)
    remote_only = svc.merged_remote_branch_names()
    return [
        "delete_mode: merged branches only (local + remote)",
        *_branch_preview_lines("merged_local_branches", local),
        *_branch_preview_lines("merged_remote_branches", remote_only, prefix="origin/"),
    ]


def _branch_delete_all_intent_lines(svc: GitShortcuts) -> list[str]:
    local = svc.local_branch_names(exclude_main=True)
    remote = svc.remote_branch_names()
    return [
        "delete_mode: all branches except main (including unmerged)",
        *_branch_preview_lines("local_branches_to_delete", local),
        *_branch_preview_lines("remote_branches_to_delete", remote, prefix="origin/"),
    ]


@branch_app.command("delete")
def branch_delete_cmd(
    name: str | None = typer.Argument(None, help="Branch to delete."),
    merged: bool = typer.Option(
        False, "--merged", help="Delete merged branches (local + remote)."
    ),
    all_branches: bool = typer.Option(
        False, "--all", help="Delete all branches except main (including unmerged)."
    ),
    force: bool = typer.Option(False, "--force", "-D"),
    remote: bool = typer.Option(True, "--remote/--no-remote"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Delete one branch, merged branches, or all branches except main."""
    if merged and all_branches:
        raise typer.BadParameter("Pass only one of --merged or --all")
    svc = _svc()
    if merged:
        _write_gate(
            "branch-delete-merged",
            yes=yes,
            question="Delete all merged branches (local and remote)?",
            extra_lines=_branch_delete_merged_intent_lines(svc),
        )
        deleted = svc.branch_delete_all_merged(yes=True)
        rprint(f"[green]deleted[/green] {len(deleted)} branch(es)")
        return
    if all_branches:
        _write_gate(
            "branch-delete-all",
            yes=yes,
            question="Delete ALL branches except main (local and remote)?",
            extra_lines=_branch_delete_all_intent_lines(svc),
        )
        deleted = svc.branch_delete_all(yes=True)
        rprint(f"[green]deleted[/green] {len(deleted)} branch(es)")
        return
    if not name:
        raise typer.BadParameter("branch name required (or pass --merged or --all)")
    _write_gate(
        "branch-delete",
        yes=yes,
        question=f"Delete branch {name}?",
        extra_lines=[f"target_branch: {name}", f"force: {force}", f"remote: {remote}"],
    )
    svc.branch_delete(name, force=force, remote=remote, yes=True)
    rprint(f"[green]deleted[/green] {name}")


@branch_app.command("clear")
def branch_clear_cmd(
    yes: bool = typer.Option(False, "--yes", "-y"),
    keep_ignored: bool = typer.Option(
        False, "--keep-ignored", help="Use git clean -fd instead of -fdx."
    ),
    delete_remote: bool = typer.Option(
        False,
        "--delete-remote",
        help="Also delete remote branches on origin (non-interactive; requires --yes).",
    ),
) -> None:
    """Reset locally, checkout main, delete all branches except main."""
    svc = _svc()
    local_preview = svc.local_branch_names(exclude_main=True)
    _write_gate(
        "branch-clear",
        yes=yes,
        question=(
            "Reset working tree, checkout main, and delete ALL local branches except main?"
        ),
        extra_lines=[
            "warning: this clears everything locally",
            *_branch_preview_lines("local_branches_to_delete", local_preview),
        ],
    )
    local_deleted = svc.clear_branches_local(yes=True, keep_ignored=keep_ignored)
    rprint(f"[green]cleared[/green] {len(local_deleted)} local branch(es)")

    remote_preview = svc.remote_branch_names()
    if not remote_preview:
        return

    do_remote = False
    if delete_remote:
        if not sys.stdin.isatty() and not yes:
            raise typer.Exit("Pass --yes with --delete-remote in non-interactive mode.")
        if sys.stdin.isatty() and not yes:
            _write_gate(
                "branch-clear-remote",
                yes=False,
                question="Also delete ALL remote branches on origin (except main)?",
                extra_lines=_branch_preview_lines(
                    "remote_branches_to_delete",
                    remote_preview,
                    prefix="origin/",
                ),
            )
            do_remote = True
        else:
            do_remote = True
    elif sys.stdin.isatty():
        snapshot = git_worktree_snapshot(svc)
        typer.echo(WRITE_GATE_DELIMITER)
        typer.echo("operation: branch-clear-remote")
        for line in snapshot.summary_lines():
            typer.echo(line)
        for line in _branch_preview_lines(
            "remote_branches_to_delete",
            remote_preview,
            prefix="origin/",
        ):
            typer.echo(line)
        typer.echo(WRITE_GATE_DELIMITER)
        do_remote = typer.confirm(
            "Also delete ALL remote branches on origin (except main)?",
            default=False,
        )

    if do_remote:
        remote_deleted = svc.delete_remote_branches(yes=True)
        rprint(f"[green]deleted[/green] {len(remote_deleted)} remote branch(es)")


@branch_app.command("current")
def branch_current_cmd() -> None:
    """Print current branch name (read-only)."""
    typer.echo(_svc().current_branch())


@branch_app.command("rename")
def branch_rename_cmd(
    new_name: str = typer.Argument(..., help="New branch name."),
) -> None:
    """Rename the current branch."""
    from gardusig_cli.utils.process import run_git

    run_git(["branch", "-m", new_name], cwd=_svc().top)
    rprint(f"[green]renamed to[/green] {new_name}")


@post_merge_app.command("cleanup")
def post_merge_cleanup_cmd(
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Align main and delete merged branches."""
    _write_gate(
        "post-merge-cleanup",
        yes=yes,
        question="Align main and delete merged branches?",
    )
    deleted = _svc().post_merge_cleanup(yes=True)
    rprint(f"[green]cleanup done[/green]; removed {len(deleted)} branches")


@git_app.command("rebase")
def rebase_cmd(
    onto: str | None = typer.Argument(None, help="Rebase onto ref (default canonical main)."),
    continue_: bool = typer.Option(False, "--continue", help="Continue rebase."),
    abort: bool = typer.Option(False, "--abort", help="Abort rebase."),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Rebase current branch."""
    svc = _svc()
    if not (continue_ or abort):
        target = onto or svc.canonical_main_ref()
        _write_gate(
            "rebase",
            yes=yes,
            question=f"Rebase onto {target}?",
            extra_lines=[f"onto: {target}"],
        )
    svc.rebase(onto, continue_=continue_, abort=abort)
    rprint("[green]rebase step complete[/green]")


@git_app.command("revert")
def revert_cmd(
    sha: str | None = typer.Argument(None),
    merge_parent: int | None = typer.Option(None, "-m", help="Merge parent for merge commits."),
    continue_: bool = typer.Option(False, "--continue"),
    abort: bool = typer.Option(False, "--abort"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Revert commit(s)."""
    if not sha and not (continue_ or abort):
        raise typer.BadParameter("sha required unless --continue/--abort")
    if sha and not (continue_ or abort):
        _write_gate(
            "revert",
            yes=yes,
            question=f"Revert commit {sha}?",
            extra_lines=[f"sha: {sha}"],
        )
    _svc().revert(sha or "", merge_parent=merge_parent, continue_=continue_, abort=abort)
    rprint("[green]revert step complete[/green]")


@cherry_app.command("pick")
def cherry_pick_cmd(
    sha: str | None = typer.Argument(None),
    continue_: bool = typer.Option(False, "--continue"),
    abort: bool = typer.Option(False, "--abort"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Cherry-pick onto current branch."""
    if not sha and not (continue_ or abort):
        raise typer.BadParameter("sha required unless --continue/--abort")
    if sha and not (continue_ or abort):
        _write_gate(
            "cherry-pick",
            yes=yes,
            question=f"Cherry-pick {sha}?",
            extra_lines=[f"sha: {sha}"],
        )
    _svc().cherry_pick(sha or "", continue_=continue_, abort=abort)
    rprint("[green]cherry-pick step complete[/green]")


def _reconcile_tag_push(
    svc: GitShortcuts,
    tag_name: str,
    *,
    yes: bool = False,
    force: bool = False,
) -> None:
    action = svc.tag_push_action(tag_name)
    if action == "missing-local":
        raise typer.Exit(f"Tag not found locally: {tag_name}")
    if action == "no-remote":
        rprint(f"[dim]skip push[/dim] (no origin remote)")
        return
    if action == "skip":
        rprint(f"[dim]skip[/dim] {tag_name} (already synced)")
        return
    if action == "push":
        if not force:
            _write_gate(
                "tag-push",
                yes=yes,
                question=f"Push tag {tag_name} to origin?",
                extra_lines=[f"tag: {tag_name}"],
            )
        svc.push_tag(tag_name, force=False)
        rprint(f"[green]pushed[/green] {tag_name}")
        return
    if force:
        svc.push_tag(tag_name, force=True)
        rprint(f"[green]force-pushed[/green] {tag_name}")
        return
    _write_gate(
        "tag-force-push",
        yes=yes,
        question=f"Tag {tag_name} differs on origin. Force-push?",
        extra_lines=[f"tag: {tag_name}", "remote: origin"],
    )
    svc.push_tag(tag_name, force=True)
    rprint(f"[green]force-pushed[/green] {tag_name}")


def _tag_list() -> None:
    svc = _svc()
    local = svc.list_local_tags()
    remote = svc.list_remote_tags()
    rprint(f"[bold]Local tags[/bold] ({len(local)}):")
    for name in local:
        rprint(f"  {name}")
    if not local:
        rprint("  (none)")
    rprint(f"[bold]Remote tags on origin[/bold] ({len(remote)}):")
    for name in remote:
        rprint(f"  {name}")
    if not remote:
        rprint("  (none)")


def _tag_create(name: str | None, *, yes: bool, force: bool = False) -> None:
    svc = _svc()
    tag_name = name or default_tag_name()
    try:
        svc.prepare_for_tag(yes=yes)
    except RuntimeError as exc:
        raise typer.Exit(str(exc)) from exc
    replace_local = False
    if svc.tag_exists_local(tag_name):
        if force:
            replace_local = True
        else:
            _write_gate(
                "tag-replace",
                yes=yes,
                question=f"Tag {tag_name} exists locally. Replace it?",
                extra_lines=[f"tag: {tag_name}"],
            )
            replace_local = True
    svc.create_tag(tag_name, replace=replace_local)
    _reconcile_tag_push(svc, tag_name, yes=yes, force=force)
    rprint(f"[green]tag[/green] {tag_name}")


@git_app.command("tag")
def tag_cmd(
    action: str | None = typer.Argument(None, help="list, push, or tag name (default: create today)."),
    name: str | None = typer.Argument(None, help="Tag name for push, or explicit create name."),
    yes: bool = typer.Option(False, "--yes", "-y"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Replace an existing local tag and/or force-push when remote differs.",
    ),
) -> None:
    """Create tag on main (default today), or: tag list | tag push [NAME]."""
    if action == "list":
        _tag_list()
        return
    if action == "push":
        _reconcile_tag_push(_svc(), name or default_tag_name(), yes=yes, force=force)
        return
    _tag_create(action, yes=yes, force=force)


@git_app.command("zip")
def zip_cmd(
    tag: str | None = typer.Argument(None, help="Tag to archive (default today YYYY-MM-DD)."),
    output: Path | None = typer.Option(
        None,
        "-o",
        "--output",
        help="Output zip path (default git-tags/REPO/REPO-TAG.zip in backup.tags_dir).",
    ),
) -> None:
    """Create a zip archive of the tree at a git tag."""
    svc = _svc()
    tag_name = tag or default_tag_name()
    if not svc.tag_exists_local(tag_name):
        raise typer.Exit(f"Tag not found: {tag_name}. Run `cli git tag` first.")
    dest = output or default_zip_path(svc.repo_basename(), tag_name)
    repo_path = Path(svc.top)
    encrypted = repo_encrypt_backup(repo_path)
    password = require_backup_zip_password() if encrypted else None
    archive_tag_zip(repo_path, tag_name, dest, encrypted=encrypted, password=password)
    mode = "encrypted zip" if encrypted else "git archive"
    stem = tag_zip_basename(svc.repo_basename(), tag_name)
    rprint(f"[green]zip[/green] git-tags/{svc.repo_basename()}/{stem}.zip ({mode})")


@git_app.command("review")
def review_cmd(
    no_install: bool = typer.Option(False, "--no-install", help="Skip bootstrap if venv missing."),
    quick: bool = typer.Option(
        False,
        "--quick",
        help="Shell syntax only; skip Docker unit tests.",
    ),
) -> None:
    """Workspace health: shell syntax checks and Docker unit tests (@git-review)."""
    code = run_review(install=not no_install, quick=quick)
    if code == 0:
        rprint("[green]review passed[/green]")
        raise typer.Exit()
    rprint("[red]review failed[/red]")
    raise typer.Exit(code=code)


@git_app.command("docs")
def docs_cmd() -> None:
    """List doc paths for sync (@git-docs; AI-driven edits via cursor-skills)."""
    root = project_root()
    docs_dir = root / "docs"
    readme = root / "README.md"
    rprint("[bold]Documentation inventory[/bold] (edit via cursor-skills @git-docs):")
    if readme.exists():
        rprint(f"  {readme.relative_to(root)}")
    if docs_dir.is_dir():
        for path in sorted(docs_dir.rglob("*.md")):
            rprint(f"  {path.relative_to(root)}")
    rprint("[dim]No files modified. Run @git-docs in Cursor for in-place doc updates.[/dim]")


@large_app.command("files")
def large_files_cmd(
    top_n: int = typer.Option(20, "-n", "--top"),
    worktree: bool = typer.Option(False, "--worktree", help="Scan worktree instead of tracked files."),
) -> None:
    """List largest files in the repo."""
    rows = _svc().large_files(top_n, worktree=worktree)
    for size, path in rows:
        rprint(f"{size:>12}  {path}")


@diff_app.command("stat")
def diff_stat_cmd(
    base: str = typer.Option(..., "--base", help="Base ref for three-dot diff stat."),
    head: str = typer.Option("HEAD", "--head"),
) -> None:
    """Diff stat vs base (read-only)."""
    typer.echo(_svc().diff_stat(base, head).rstrip())


@diff_app.command("names")
def diff_names_cmd(
    base: str = typer.Option(..., "--base"),
    head: str = typer.Option("HEAD", "--head"),
) -> None:
    """Name-status diff vs base (read-only)."""
    typer.echo(_svc().diff_name_status(base, head).rstrip())


@log_app.command("oneline")
def log_oneline_cmd(
    base: str = typer.Option(..., "--base"),
    head: str = typer.Option("HEAD", "--head"),
    max_count: int | None = typer.Option(None, "--max-count"),
) -> None:
    """Oneline log for base..head (read-only)."""
    typer.echo(_svc().log_oneline(base, head, max_count=max_count).rstrip())


@log_app.command("messages")
def log_messages_cmd(
    base: str = typer.Option(..., "--base"),
    head: str = typer.Option("HEAD", "--head"),
    max_count: int | None = typer.Option(None, "--max-count"),
) -> None:
    """Full commit subject/body log for base..head (read-only)."""
    typer.echo(_svc().log_messages(base, head, max_count=max_count).rstrip())


@rev_list_app.command("count")
def rev_list_count_cmd(
    base: str = typer.Option(..., "--base"),
    head: str = typer.Option("HEAD", "--head"),
) -> None:
    """Ahead/behind counts for base...head (read-only)."""
    left, right = _svc().rev_list_count(base, head)
    typer.echo(json.dumps({"behind": left, "ahead": right}))


@remote_app.command("url")
def remote_url_cmd(
    name: str = typer.Argument("origin", help="Remote name"),
) -> None:
    """Print remote URL (read-only)."""
    typer.echo(_svc().remote_url(name))


@rev_app.command("parse")
def rev_parse_cmd(
    ref: str = typer.Argument(..., help="Git ref to resolve"),
) -> None:
    """Resolve ref to SHA (read-only)."""
    typer.echo(_svc().rev_parse(ref))


@merge_base_app.command("check")
def merge_base_check_cmd(
    base: str = typer.Option(..., "--base"),
    head: str = typer.Option("HEAD", "--head"),
) -> None:
    """True when base is ancestor of head (read-only)."""
    typer.echo(json.dumps({"is_ancestor": _svc().merge_base_is_ancestor(base, head)}))


@git_publish_app.command("check")
def publish_check_cmd(
    remote: str = typer.Option("origin", "--remote"),
    branch: str | None = typer.Option(None, "--branch"),
) -> None:
    """Check whether HEAD is on remote branch (read-only)."""
    svc = _svc()
    br = branch or svc.current_branch()
    head = svc.rev_parse("HEAD")
    on_remote = svc.commit_on_remote_branch(remote, br, head)
    typer.echo(json.dumps({"branch": br, "commit": head, "on_remote": on_remote}))


post_app.add_typer(post_merge_app, name="merge")
git_app.add_typer(branch_app, name="branch")
git_app.add_typer(diff_app, name="diff")
git_app.add_typer(log_app, name="log")
git_app.add_typer(rev_app, name="rev")
git_app.add_typer(rev_list_app, name="rev-list")
git_app.add_typer(remote_app, name="remote")
git_app.add_typer(merge_base_app, name="merge-base")
git_app.add_typer(git_publish_app, name="publish")
git_app.add_typer(large_app, name="large")
git_app.add_typer(post_app, name="post")
git_app.add_typer(cherry_app, name="cherry")
