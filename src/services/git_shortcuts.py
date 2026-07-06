from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from src.utils.process import GitCommandError, run_git
from src.utils.quick_defaults import suggest_branch_name

# Remotes consulted for canonical main (fork workflow: upstream → fork → origin).
MAIN_REMOTES = ("upstream", "fork", "origin")


@dataclass(frozen=True)
class GitPushPlan:
    """Resolved push intent before the write gate."""

    source_branch: str
    target_branch: str
    remote: str | None
    dirty: bool
    message: str
    allow_main: bool = False
    create_branch_first: bool = False
    warnings: tuple[str, ...] = ()

    @property
    def will_push(self) -> bool:
        return self.remote is not None


@dataclass(frozen=True)
class GitPushResult:
    """Outcome of `cli git push` after local commit/push work."""

    branch: str
    pushed: bool
    remote: str | None
    created_branch: bool = False
    committed: bool = False
    warnings: tuple[str, ...] = ()


class GitShortcuts:
    """Local git operations with safety gates for destructive actions."""

    def __init__(self, top: str | None = None) -> None:
        self.top = top or os.environ.get("CLI_GIT_ROOT") or self.repo_root()

    @staticmethod
    def repo_root() -> str:
        return run_git(["rev-parse", "--show-toplevel"]).stdout.strip()

    def current_branch(self) -> str:
        return run_git(["branch", "--show-current"], cwd=self.top).stdout.strip()

    def is_detached_head(self) -> bool:
        result = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=self.top, check=False)
        if result.returncode != 0:
            return True
        ref = result.stdout.strip()
        return ref == "HEAD" or not ref

    def is_branch_merged_into_main(self, branch: str) -> bool:
        if not branch or branch == "main":
            return False
        return branch in self.merged_branch_names(include_current=True)

    def push_warnings(self, *, branch: str | None = None, allow_main: bool = False) -> list[str]:
        """Informational warnings before push (never blocks without the write gate)."""
        branch = branch or self.current_branch()
        warnings: list[str] = []
        if branch == "main":
            if allow_main:
                tracking = self.tracking_branch()
                if tracking and tracking != "main":
                    warnings.append(f"on main but upstream tracks {tracking!r}")
            return warnings
        if not branch:
            return warnings
        if self.is_branch_merged_into_main(branch):
            warnings.append(f"branch {branch!r} is already merged into main")
        if self.remote_exists("origin") and not self.has_upstream():
            warnings.append(f"branch {branch!r} has no upstream; push will set origin HEAD")
        return warnings

    def status_short(self) -> str:
        return run_git(["status", "--short"], cwd=self.top).stdout

    def is_dirty(self) -> bool:
        return bool(self.status_short().strip())

    def has_upstream(self) -> bool:
        result = run_git(
            ["rev-parse", "--abbrev-ref", "@{u}"],
            cwd=self.top,
            check=False,
        )
        return result.returncode == 0

    def tracking_branch(self) -> str | None:
        """Local branch name tracked by @{u}, if any."""
        result = run_git(
            ["rev-parse", "--abbrev-ref", "@{u}"],
            cwd=self.top,
            check=False,
        )
        if result.returncode != 0:
            return None
        ref = result.stdout.strip()
        if "/" in ref:
            return ref.split("/", 1)[1]
        return ref or None

    def remote_exists(self, name: str = "origin") -> bool:
        result = run_git(["remote", "get-url", name], cwd=self.top, check=False)
        return result.returncode == 0

    def canonical_main_ref(self) -> str:
        for remote in MAIN_REMOTES:
            if self._remote_main_ref_exists(remote):
                return f"{remote}/main"
        return "main"

    def _remote_main_ref_exists(self, remote: str) -> bool:
        if not self.remote_exists(remote):
            return False
        result = run_git(["rev-parse", f"{remote}/main"], cwd=self.top, check=False)
        return result.returncode == 0

    def available_main_refs(self) -> list[str]:
        refs: list[str] = []
        for remote in MAIN_REMOTES:
            if self._remote_main_ref_exists(remote):
                refs.append(f"{remote}/main")
        if run_git(["rev-parse", "main"], cwd=self.top, check=False).returncode == 0:
            refs.append("main")
        return refs

    def best_main_ref(self) -> str:
        """Newest main tip among upstream/fork/origin/main (cleanest closest to latest)."""
        refs = self.available_main_refs()
        if not refs:
            return "main"
        if len(refs) == 1:
            return refs[0]
        best = refs[0]
        best_time = -1
        for ref in refs:
            result = run_git(["log", "-1", "--format=%ct", ref], cwd=self.top, check=False)
            if result.returncode != 0:
                continue
            try:
                ts = int(result.stdout.strip())
            except ValueError:
                continue
            if ts > best_time:
                best_time = ts
                best = ref
        return best

    def fetch_all(self, *, prune: bool = False) -> None:
        seen: set[str] = set()
        for remote in (*MAIN_REMOTES, "origin", "upstream", "fork"):
            if remote in seen or not self.remote_exists(remote):
                continue
            seen.add(remote)
            args = ["fetch", remote]
            if prune:
                args.append("--prune")
            run_git(args, cwd=self.top)

    def checkout_main(self) -> None:
        result = run_git(["checkout", "main"], cwd=self.top, check=False)
        if result.returncode != 0:
            if self.remote_exists("origin"):
                run_git(["checkout", "-B", "main", "origin/main"], cwd=self.top)
            else:
                raise GitCommandError(
                    ["git", "checkout", "main"],
                    result.returncode,
                    result.stderr,
                )

    def _clean_exclude_args(self) -> list[str]:
        """Skip active venv during git clean -fdx (avoid deleting the running interpreter)."""
        excludes: list[str] = []
        seen: set[str] = set()
        repo = Path(self.top).resolve()

        def add_exclude(rel: str) -> None:
            if rel and rel not in seen:
                seen.add(rel)
                excludes.extend(["-e", rel])

        venv = os.environ.get("VIRTUAL_ENV")
        if venv:
            try:
                add_exclude(Path(venv).resolve().relative_to(repo).as_posix())
            except ValueError:
                pass

        if (repo / ".venv").is_dir():
            add_exclude(".venv")

        return excludes

    def clean_worktree(self, *, keep_ignored: bool = False) -> None:
        """Remove untracked/ignored build and test artifacts (git clean -fdx; keeps .venv)."""
        self._clean_worktree(keep_ignored=keep_ignored)

    def _clean_worktree(self, *, keep_ignored: bool) -> None:
        if keep_ignored:
            run_git(["clean", "-fd"], cwd=self.top)
            return
        run_git(["clean", "-fdx", *self._clean_exclude_args()], cwd=self.top)

    def sync_main(self, *, yes: bool = False, keep_ignored: bool = False) -> None:
        """Checkout main, fetch remotes, hard-reset to newest main tip, clean worktree."""
        if self.is_dirty() and not yes:
            raise RuntimeError(
                "Working tree is dirty. Re-run with --yes to discard local changes."
            )
        self.checkout_main()
        self.fetch_all()
        ref = self.best_main_ref()
        run_git(["rev-parse", ref], cwd=self.top)
        run_git(["reset", "--hard", ref], cwd=self.top)
        self._clean_worktree(keep_ignored=keep_ignored)

    def align_main(self, *, yes: bool = False, keep_ignored: bool = False) -> None:
        self.sync_main(yes=yes, keep_ignored=keep_ignored)

    def _prepare_leave_branch(self, *, message: str, discard: bool) -> None:
        if self.current_branch() == "main" or not self.is_dirty():
            return
        if discard:
            run_git(["reset", "--hard", "HEAD"], cwd=self.top)
            run_git(["clean", "-fd", *self._clean_exclude_args()], cwd=self.top)
            return
        self.commit(message)

    def commit(self, message: str = ".", *, paths: list[str] | None = None) -> bool:
        if paths:
            run_git(["add", "--", *paths], cwd=self.top)
        else:
            run_git(["add", "-A"], cwd=self.top)
        staged = run_git(["diff", "--cached", "--quiet"], cwd=self.top, check=False)
        if staged.returncode == 0:
            return False
        run_git(["commit", "-m", message], cwd=self.top)
        return True

    def push_plan(self, *, allow_main: bool = False, message: str = ".") -> GitPushPlan:
        """Resolve push intent once so prompts and writes agree."""
        current = self.current_branch()
        dirty = self.is_dirty()
        remote = "origin" if self.remote_exists("origin") else None
        create_branch = current == "main" and not allow_main and remote is not None
        target = (
            suggest_branch_name(self.local_branch_names(exclude_main=False))
            if create_branch
            else current
        )
        warnings = tuple(self.push_warnings(branch=current, allow_main=allow_main))
        return GitPushPlan(
            source_branch=current,
            target_branch=target,
            remote=remote,
            dirty=dirty,
            message=message,
            allow_main=allow_main,
            create_branch_first=create_branch,
            warnings=warnings,
        )

    def push(
        self,
        *,
        allow_main: bool = False,
        message: str = ".",
        yes: bool = False,
    ) -> GitPushResult:
        """Stage if dirty, commit, and push when a remote is available."""
        if not yes:
            raise RuntimeError("Push requires confirmation. Pass --yes to proceed.")
        plan = self.push_plan(allow_main=allow_main, message=message)
        created_branch = False
        if plan.create_branch_first:
            self.start(plan.target_branch, yes=True, prep=False)
            created_branch = True
        committed = False
        if plan.dirty:
            committed = self.commit(message)
        if plan.remote is None:
            return GitPushResult(
                branch=self.current_branch(),
                pushed=False,
                remote=None,
                created_branch=created_branch,
                committed=committed,
                warnings=plan.warnings,
            )
        run_git(["push", "-u", plan.remote, "HEAD"], cwd=self.top)
        return GitPushResult(
            branch=self.current_branch(),
            pushed=True,
            remote=plan.remote,
            created_branch=created_branch,
            committed=committed,
            warnings=plan.warnings,
        )

    def pull(self, *, merge_branch: str | None = None) -> None:
        self.fetch_all()
        main_ref = self.best_main_ref()
        if self.current_branch() == "main":
            run_git(["rev-parse", main_ref], cwd=self.top)
            run_git(["reset", "--hard", main_ref], cwd=self.top)
            return
        if self.has_upstream():
            run_git(["merge", "@{u}"], cwd=self.top)
        run_git(["rev-parse", main_ref], cwd=self.top)
        if merge_branch:
            run_git(["merge", merge_branch], cwd=self.top)
        else:
            run_git(["merge", main_ref], cwd=self.top)

    def start(
        self,
        branch: str | None = None,
        *,
        yes: bool = False,
        keep_ignored: bool = False,
        prep: bool = True,
        no_push: bool = True,
        message: str = ".",
    ) -> str:
        """Create a feature branch. With prep (default), align main first — issue workflow."""
        if prep:
            self.align_main(yes=yes, keep_ignored=keep_ignored)
        name = branch or suggest_branch_name(self.local_branch_names(exclude_main=False))
        run_git(["checkout", "-b", name], cwd=self.top)
        if not no_push:
            self.push(message=message, yes=yes)
        return name

    def stash_push(self, message: str | None = None) -> None:
        args = ["stash", "push"]
        if message:
            args.extend(["-m", message])
        run_git(args, cwd=self.top)

    def stash_list(self) -> str:
        return run_git(["stash", "list"], cwd=self.top).stdout

    def stash_apply(self, index: int = 0) -> None:
        run_git(["stash", "apply", f"stash@{{{index}}}"], cwd=self.top)

    def stash_pop(self, index: int = 0) -> None:
        run_git(["stash", "pop", f"stash@{{{index}}}"], cwd=self.top)

    def stash_drop(self, index: int = 0, *, yes: bool = False) -> None:
        if not yes:
            raise RuntimeError("Pass --yes to drop a stash entry.")
        run_git(["stash", "drop", f"stash@{{{index}}}"], cwd=self.top)

    def stash_clear(self, *, yes: bool = False) -> None:
        if not yes:
            raise RuntimeError("Pass --yes to clear all stashes.")
        run_git(["stash", "clear"], cwd=self.top)

    def branch_list(self) -> str:
        return run_git(["branch", "-a", "-vv"], cwd=self.top).stdout

    def branch_prune(self) -> None:
        self.fetch_all(prune=True)

    def branch_delete(
        self,
        name: str,
        *,
        force: bool = False,
        remote: bool = True,
        yes: bool = False,
    ) -> None:
        if not yes:
            raise RuntimeError("Pass --yes to delete a branch.")
        current = self.current_branch()
        if name == current:
            raise RuntimeError(f"Cannot delete current branch: {name}")
        flag = "-D" if force else "-d"
        run_git(["branch", flag, name], cwd=self.top)
        if remote and self.remote_exists("origin"):
            run_git(["push", "origin", "--delete", name], cwd=self.top, check=False)

    def merged_branch_names(self, *, include_current: bool = False) -> list[str]:
        current = self.current_branch()
        protected: set[str] = {"main"}
        if not include_current:
            protected.add(current)
        main_ref = self.best_main_ref()
        out = run_git(["branch", "--merged", main_ref], cwd=self.top).stdout
        names: list[str] = []
        for line in out.splitlines():
            name = line.strip().lstrip("* ").strip()
            if name and name not in protected:
                names.append(name)
        return sorted(names)

    def merged_remote_branch_names(self, remote: str = "origin") -> list[str]:
        """Remote branches merged into main that have no local branch."""
        if not self.remote_exists(remote):
            return []
        main_ref = self.best_main_ref()
        out = run_git(["branch", "-r", "--merged", main_ref], cwd=self.top).stdout
        local_names = set(self.local_branch_names(exclude_main=False))
        remote_prefix = f"{remote}/"
        protected = {"main", "HEAD"}
        names: list[str] = []
        for line in out.splitlines():
            ref = line.strip().lstrip("* ").strip()
            if not ref.startswith(remote_prefix):
                continue
            short = ref[len(remote_prefix) :]
            if short in protected or short in local_names:
                continue
            names.append(short)
        return sorted(set(names))

    def branch_delete_all_merged(self, *, yes: bool = False) -> list[str]:
        if not yes:
            raise RuntimeError("Pass --yes to delete merged branches.")
        self.branch_prune()
        deleted: list[str] = []
        for name in self.merged_branch_names():
            self.branch_delete(name, force=False, remote=True, yes=True)
            deleted.append(name)
        if self.remote_exists("origin"):
            for name in self.merged_remote_branch_names():
                result = run_git(
                    ["push", "origin", "--delete", name],
                    cwd=self.top,
                    check=False,
                )
                if result.returncode == 0:
                    deleted.append(f"origin/{name}")
        return deleted

    def branch_delete_all(self, *, yes: bool = False) -> list[str]:
        """Delete every branch except main (local and remote), including unmerged."""
        if not yes:
            raise RuntimeError("Pass --yes to delete all branches.")
        self.branch_prune()
        if self.current_branch() != "main":
            if self.is_dirty():
                raise RuntimeError(
                    "Checkout main first (working tree is dirty), or stash/commit changes."
                )
            run_git(["checkout", "main"], cwd=self.top)
        deleted: list[str] = []
        deleted.extend(self.delete_all_local_branches(yes=True))
        for name in self.delete_remote_branches(yes=True):
            deleted.append(f"origin/{name}")
        return deleted

    def reset(
        self,
        *,
        yes: bool = False,
        keep_ignored: bool = False,
        main_only: bool = False,
        all_local: bool = False,
        delete_merged: bool = False,
        branch_message: str = ".",
        discard: bool = False,
    ) -> list[str]:
        """Return to synced main; optional branch cleanup when flags are set."""
        if not yes:
            raise RuntimeError("Pass --yes to reset.")
        self._prepare_leave_branch(message=branch_message, discard=discard)
        self.sync_main(yes=True, keep_ignored=keep_ignored)
        if main_only:
            return []
        if all_local:
            return self.delete_all_local_branches(yes=True)
        if delete_merged:
            return self.branch_delete_all_merged(yes=True)
        return []

    def delete_all_local_branches(self, *, yes: bool = False) -> list[str]:
        if not yes:
            raise RuntimeError("Pass --yes to delete all local branches.")
        deleted: list[str] = []
        for name in self.local_branch_names(exclude_main=True):
            run_git(["branch", "-D", name], cwd=self.top)
            deleted.append(name)
        return deleted

    def post_merge_cleanup(self, *, yes: bool = False) -> list[str]:
        self.reset(yes=yes, main_only=True)
        return self.branch_delete_all_merged(yes=True)

    def local_branch_names(self, *, exclude_main: bool = True) -> list[str]:
        out = run_git(
            ["for-each-ref", "--format=%(refname:short)", "refs/heads/"],
            cwd=self.top,
        ).stdout
        names = [line.strip() for line in out.splitlines() if line.strip()]
        if exclude_main:
            names = [name for name in names if name != "main"]
        return sorted(names)

    def remote_branch_names(self, remote: str = "origin") -> list[str]:
        if not self.remote_exists(remote):
            return []
        out = run_git(
            ["for-each-ref", "--format=%(refname)", f"refs/remotes/{remote}/"],
            cwd=self.top,
            check=False,
        ).stdout
        remote_prefix = f"refs/remotes/{remote}/"
        names: list[str] = []
        for line in out.splitlines():
            ref = line.strip()
            if not ref or not ref.startswith(remote_prefix):
                continue
            short = ref[len(remote_prefix) :]
            # Skip origin/HEAD symref (refname:short would appear as bare "origin").
            if short in {"HEAD", "main"}:
                continue
            names.append(short)
        return sorted(set(names))

    def clear_branches_local(
        self,
        *,
        yes: bool = False,
        keep_ignored: bool = False,
    ) -> list[str]:
        """Align main (reset + clean), then delete every local branch except main."""
        if not yes:
            raise RuntimeError("Pass --yes to clear all local branches.")
        self.align_main(yes=True, keep_ignored=keep_ignored)
        deleted: list[str] = []
        for name in self.local_branch_names(exclude_main=True):
            run_git(["branch", "-D", name], cwd=self.top)
            deleted.append(name)
        return deleted

    def delete_remote_branches(self, *, yes: bool = False, remote: str = "origin") -> list[str]:
        if not yes:
            raise RuntimeError("Pass --yes to delete remote branches.")
        if not self.remote_exists(remote):
            return []
        self.fetch_all(prune=True)
        deleted: list[str] = []
        for name in self.remote_branch_names(remote):
            result = run_git(
                ["push", remote, "--delete", name],
                cwd=self.top,
                check=False,
            )
            if result.returncode == 0:
                deleted.append(name)
        return deleted

    def rebase(
        self,
        onto: str | None = None,
        *,
        continue_: bool = False,
        abort: bool = False,
    ) -> None:
        if abort:
            run_git(["rebase", "--abort"], cwd=self.top)
            return
        if continue_:
            run_git(["rebase", "--continue"], cwd=self.top)
            return
        target = onto or self.canonical_main_ref()
        self.fetch_all()
        run_git(["rebase", target], cwd=self.top)

    def revert(
        self,
        sha: str,
        *,
        merge_parent: int | None = None,
        continue_: bool = False,
        abort: bool = False,
    ) -> None:
        if abort:
            run_git(["revert", "--abort"], cwd=self.top)
            return
        if continue_:
            run_git(["revert", "--continue"], cwd=self.top)
            return
        args = ["revert", "--no-edit"]
        if merge_parent is not None:
            args.extend(["-m", str(merge_parent)])
        args.append(sha)
        run_git(args, cwd=self.top)

    def cherry_pick(
        self,
        sha: str,
        *,
        continue_: bool = False,
        abort: bool = False,
    ) -> None:
        if abort:
            run_git(["cherry-pick", "--abort"], cwd=self.top)
            return
        if continue_:
            run_git(["cherry-pick", "--continue"], cwd=self.top)
            return
        run_git(["cherry-pick", "--no-edit", sha], cwd=self.top)

    def head_sha(self) -> str:
        return run_git(["rev-parse", "HEAD"], cwd=self.top).stdout.strip()

    def main_tip_sha(self) -> str:
        """Latest main commit: best remote/local main tip."""
        ref = self.best_main_ref()
        return run_git(["rev-parse", ref], cwd=self.top).stdout.strip()

    def prepare_for_tag(self, *, yes: bool = False) -> None:
        """Align to latest main (like reset) and verify HEAD before tagging."""
        if self.is_dirty() and not yes:
            raise RuntimeError(
                "Working tree is dirty. Pass --yes to align main and tag, "
                "or run `cli git reset --yes` first."
            )
        if yes and self.is_dirty():
            if self.current_branch() == "main":
                self.commit(".")
            else:
                self._prepare_leave_branch(message=".", discard=False)
        self.sync_main(yes=yes, keep_ignored=False)
        if self.current_branch() != "main":
            raise RuntimeError("Expected to be on main after sync.")
        head = self.head_sha()
        tip = self.main_tip_sha()
        if head != tip:
            raise RuntimeError(
                f"Cannot tag: HEAD ({head[:7]}) is not the latest main commit ({tip[:7]}). "
                "Run `cli git reset --yes` and retry."
            )

    def tag_exists_local(self, name: str) -> bool:
        result = run_git(
            ["rev-parse", "-q", "--verify", f"refs/tags/{name}"],
            cwd=self.top,
            check=False,
        )
        return result.returncode == 0

    def tag_exists_remote(self, name: str, remote: str = "origin") -> bool:
        if not self.remote_exists(remote):
            return False
        result = run_git(
            ["ls-remote", "--tags", remote, f"refs/tags/{name}"],
            cwd=self.top,
            check=False,
        )
        return bool(result.stdout.strip())

    def create_tag(self, name: str, *, replace: bool = False) -> None:
        if self.tag_exists_local(name):
            if not replace:
                raise RuntimeError(
                    f"Tag {name} already exists locally. Pass replace=True to overwrite."
                )
            run_git(["tag", "-fa", name, "HEAD", "-m", name], cwd=self.top)
        else:
            run_git(["tag", "-a", name, "HEAD", "-m", name], cwd=self.top)

    def push_tag(self, name: str, *, force: bool = False, remote: str = "origin") -> None:
        if not self.remote_exists(remote):
            raise RuntimeError(f"Remote {remote} is not configured.")
        if force:
            run_git(["push", "--force", remote, f"refs/tags/{name}"], cwd=self.top)
        else:
            run_git(["push", remote, f"refs/tags/{name}"], cwd=self.top)

    def repo_basename(self) -> str:
        return Path(self.top).name

    def list_local_tags(self) -> list[str]:
        result = run_git(["tag", "-l"], cwd=self.top, check=False)
        return sorted(line.strip() for line in result.stdout.splitlines() if line.strip())

    def list_remote_tags(self, remote: str = "origin") -> list[str]:
        if not self.remote_exists(remote):
            return []
        result = run_git(["ls-remote", "--tags", remote], cwd=self.top, check=False)
        tags: set[str] = set()
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            ref = parts[1]
            if ref.endswith("^{}"):
                continue
            if ref.startswith("refs/tags/"):
                tags.add(ref.removeprefix("refs/tags/"))
        return sorted(tags)

    def all_tag_names(self, remote: str = "origin") -> list[str]:
        """Union of local and remote tag names (sorted)."""
        return sorted(set(self.list_local_tags()) | set(self.list_remote_tags(remote)))

    def tag_local_sha(self, name: str) -> str | None:
        result = run_git(
            ["rev-parse", "-q", f"refs/tags/{name}"],
            cwd=self.top,
            check=False,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()

    def tag_remote_sha(self, name: str, remote: str = "origin") -> str | None:
        if not self.remote_exists(remote):
            return None
        result = run_git(
            ["ls-remote", remote, f"refs/tags/{name}"],
            cwd=self.top,
            check=False,
        )
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 1 and not parts[0].endswith("^{}"):
                return parts[0]
        return None

    def tag_push_action(self, name: str, remote: str = "origin") -> str:
        """Return: missing-local, no-remote, skip, push, or force."""
        if not self.tag_exists_local(name):
            return "missing-local"
        if not self.remote_exists(remote):
            return "no-remote"
        if not self.tag_exists_remote(name, remote):
            return "push"
        local_sha = self.tag_local_sha(name)
        remote_sha = self.tag_remote_sha(name, remote)
        if local_sha and remote_sha and local_sha == remote_sha:
            return "skip"
        return "force"

    def zip_tag(self, tag: str, output: Path) -> Path:
        run_git(["rev-parse", "-q", "--verify", f"refs/tags/{tag}"], cwd=self.top)
        output.parent.mkdir(parents=True, exist_ok=True)
        run_git(
            ["archive", "--format=zip", f"--output={output}", tag],
            cwd=self.top,
        )
        return output

    def large_files(self, top_n: int = 20, *, worktree: bool = False) -> list[tuple[int, str]]:
        root = Path(self.top)
        files: list[tuple[int, Path]] = []
        if worktree:
            for path in root.rglob("*"):
                if path.is_file() and ".git" not in path.parts:
                    try:
                        files.append((path.stat().st_size, path))
                    except OSError:
                        pass
        else:
            out = run_git(["ls-files", "-z"], cwd=self.top).stdout
            for part in out.split("\0"):
                if not part:
                    continue
                p = root / part
                if p.is_file():
                    try:
                        files.append((p.stat().st_size, p))
                    except OSError:
                        pass
        files.sort(reverse=True)
        return [(size, str(path.relative_to(root))) for size, path in files[:top_n]]

    def diff_stat(self, base: str, head: str = "HEAD") -> str:
        return run_git(["diff", "--stat", f"{base}...{head}"], cwd=self.top).stdout

    def diff_name_status(self, base: str, head: str = "HEAD") -> str:
        return run_git(["diff", "--name-status", f"{base}...{head}"], cwd=self.top).stdout

    def log_oneline(self, base: str, head: str = "HEAD", *, max_count: int | None = None) -> str:
        args = ["log", "--oneline", f"{base}..{head}"]
        if max_count is not None:
            args.extend(["-n", str(max_count)])
        return run_git(args, cwd=self.top).stdout

    def log_messages(self, base: str, head: str = "HEAD", *, max_count: int | None = None) -> str:
        args = ["log", "--pretty=format:---%n%s%n%n%b", f"{base}..{head}"]
        if max_count is not None:
            args.extend(["-n", str(max_count)])
        return run_git(args, cwd=self.top).stdout

    def rev_list_count(self, base: str, head: str = "HEAD") -> tuple[int, int]:
        out = run_git(
            ["rev-list", "--left-right", "--count", f"{base}...{head}"],
            cwd=self.top,
        ).stdout.strip()
        left, right = out.split()
        return int(left), int(right)

    def remote_url(self, name: str) -> str:
        return run_git(["remote", "get-url", name], cwd=self.top).stdout.strip()

    def rev_parse(self, ref: str) -> str:
        return run_git(["rev-parse", ref], cwd=self.top).stdout.strip()

    def merge_base_is_ancestor(self, base: str, head: str = "HEAD") -> bool:
        result = run_git(
            ["merge-base", "--is-ancestor", base, head],
            cwd=self.top,
            check=False,
        )
        return result.returncode == 0

    def commit_on_remote_branch(self, remote: str, branch: str, commit: str) -> bool:
        ref = f"refs/remotes/{remote}/{branch}"
        result = run_git(["merge-base", "--is-ancestor", commit, ref], cwd=self.top, check=False)
        return result.returncode == 0
