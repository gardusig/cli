"""One-shot GitHub PR shortcut orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.services.gh_service import GhService
from src.services.git_shortcuts import GitPushPlan, GitPushResult, GitShortcuts
from src.utils.process import run_git


@dataclass(frozen=True)
class PrTemplate:
    name: str
    body: str
    source: str


@dataclass(frozen=True)
class PrShortcutPlan:
    title: str
    body: str
    body_source: str
    template: str | None
    no_push: bool
    allow_main: bool
    push_plan: GitPushPlan
    needs_push: bool
    branch: str

    def summary_lines(self) -> list[str]:
        intent_parts = []
        if self.needs_push and not self.no_push:
            intent_parts.append("git add → commit/push")
        elif self.no_push:
            intent_parts.append("skip push (--no-push)")
        else:
            intent_parts.append("branch already published")
        intent_parts.append(f"gh pr create (title {self.title!r})")
        return [
            f"branch: {self.branch}",
            f"dirty: {self.push_plan.dirty}",
            f"remote: {self.push_plan.remote or '(none)'}",
            f"needs_push: {self.needs_push}",
            f"no_push: {self.no_push}",
            f"title: {self.title}",
            f"body_source: {self.body_source}",
            f"intent: {' → '.join(intent_parts)}",
            *(f"warning: {w}" for w in self.push_plan.warnings),
        ]


class GhPrShortcut:
    def __init__(
        self,
        *,
        gh: GhService | None = None,
        git: GitShortcuts | None = None,
        repo_root: Path | None = None,
    ) -> None:
        self.gh = gh or GhService()
        self.git = git or GitShortcuts()
        self.repo_root = repo_root or Path(self.git.top)

    def plan(
        self,
        *,
        title: str = ".",
        body: str = "",
        template: str | None = None,
        no_push: bool = False,
        allow_main: bool = False,
    ) -> PrShortcutPlan:
        push_plan = self.git.push_plan(allow_main=allow_main, message=".")
        resolved_body, body_source = self.resolve_body(body=body, template=template)
        needs_push = self._needs_push(push_plan)
        return PrShortcutPlan(
            title=title,
            body=resolved_body,
            body_source=body_source,
            template=template,
            no_push=no_push,
            allow_main=allow_main,
            push_plan=push_plan,
            needs_push=needs_push,
            branch=push_plan.target_branch,
        )

    def create(
        self,
        plan: PrShortcutPlan,
        *,
        yes: bool = False,
    ) -> dict[str, Any]:
        if not yes:
            raise RuntimeError("PR shortcut requires confirmation. Pass --yes to proceed.")
        if plan.no_push and plan.needs_push:
            raise RuntimeError(
                "Branch is not ready for PR creation with --no-push. "
                "Publish it first or rerun without --no-push."
            )
        push_result: GitPushResult | None = None
        if plan.needs_push:
            push_result = self.git.push(allow_main=plan.allow_main, message=".", yes=True)
            if not push_result.pushed:
                raise RuntimeError("No origin remote configured; cannot create a GitHub PR.")
        branch = push_result.branch if push_result else plan.branch
        existing = self.find_open_pr_for_branch(branch)
        if existing is not None:
            return {
                "url": existing.get("url"),
                "number": existing.get("number"),
                "title": existing.get("title"),
                "pushed": bool(push_result and push_result.pushed),
                "branch": branch,
                "body_source": plan.body_source,
                "existing": True,
            }
        data = self.gh.pr_create(title=plan.title, body=plan.body)
        data["pushed"] = bool(push_result and push_result.pushed)
        data["branch"] = branch
        data["body_source"] = plan.body_source
        data["existing"] = False
        return data

    def find_open_pr_for_branch(self, branch: str) -> dict[str, Any] | None:
        """Return an open PR whose head ref matches branch, if any."""
        candidates: list[str] = [branch]
        try:
            payload = self.gh.repo_view(fields="nameWithOwner,owner")
            owner = ""
            if isinstance(payload.get("owner"), dict):
                owner = str(payload["owner"].get("login") or "")
            name_with_owner = str(payload.get("nameWithOwner") or "")
            if not owner and "/" in name_with_owner:
                owner = name_with_owner.split("/", 1)[0]
            if owner:
                candidates.append(f"{owner}:{branch}")
        except Exception:
            pass
        seen: set[int] = set()
        for head in candidates:
            try:
                rows = self.gh.pr_list(state="open", head=head, limit=10)
            except Exception:
                continue
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                number = row.get("number")
                if number is None:
                    continue
                number = int(number)
                if number in seen:
                    continue
                if str(row.get("headRefName") or "") == branch:
                    seen.add(number)
                    return row
        return None

    def upsert_branch_pr(
        self,
        *,
        branch: str,
        title: str,
        body: str,
        base: str = "main",
        message: str,
        close_when_clean: bool = False,
    ) -> dict[str, Any]:
        """Commit dirty work to a fixed branch and create/update its single open PR."""
        existing = self.find_open_pr_for_branch(branch)
        if not self.git.is_dirty():
            if close_when_clean and existing is not None:
                self.gh.pr_close(int(existing["number"]))
                return {
                    "action": "closed",
                    "number": existing["number"],
                    "branch": branch,
                    "changed": False,
                }
            return {
                "action": "noop",
                "number": existing.get("number") if existing else None,
                "branch": branch,
                "changed": False,
            }

        run_git(["checkout", "-B", branch], cwd=self.repo_root)
        committed = self.git.commit(message)
        run_git(["push", "--force-with-lease", "-u", "origin", branch], cwd=self.repo_root)

        existing = self.find_open_pr_for_branch(branch)
        if existing is not None:
            number = int(existing["number"])
            self.gh.pr_edit(number, title=title, body=body)
            return {
                "action": "updated",
                "number": number,
                "branch": branch,
                "committed": committed,
                "changed": True,
            }

        pr = self.gh.pr_create(title=title, body=body, base=base, head=branch)
        return {
            "action": "created",
            "number": pr.get("number"),
            "url": pr.get("url"),
            "branch": branch,
            "committed": committed,
            "changed": True,
        }

    def resolve_body(self, *, body: str, template: str | None) -> tuple[str, str]:
        if not template:
            return body, "inline" if body else "empty"
        matches = self.find_templates(template)
        if not matches:
            available = ", ".join(t.name for t in self.find_templates(None)) or "(none)"
            raise RuntimeError(f"PR template not found: {template}. Available: {available}")
        if len(matches) > 1:
            names = ", ".join(t.name for t in matches)
            raise RuntimeError(f"PR template is ambiguous: {template}. Matches: {names}")
        found = matches[0]
        return found.body, found.source

    def find_templates(self, name: str | None) -> list[PrTemplate]:
        templates = [*self._remote_templates(), *self._local_templates()]
        if name is None:
            return templates
        needle = name.casefold()
        return [
            template
            for template in templates
            if template.name.casefold() == needle
            or Path(template.name).stem.casefold() == needle
        ]

    def _remote_templates(self) -> list[PrTemplate]:
        try:
            payload = self.gh.repo_view(fields="pullRequestTemplates")
        except Exception:
            return []
        rows = payload.get("pullRequestTemplates", []) if isinstance(payload, dict) else []
        templates: list[PrTemplate] = []
        if not isinstance(rows, list):
            return templates
        for row in rows:
            if isinstance(row, str):
                templates.append(PrTemplate(name=Path(row).stem, body="", source=f"remote:{row}"))
                continue
            if not isinstance(row, dict):
                continue
            raw_name = row.get("name") or row.get("filename") or row.get("path")
            if not raw_name:
                continue
            body = str(row.get("body") or row.get("content") or "")
            source = f"remote:{raw_name}"
            templates.append(PrTemplate(name=Path(str(raw_name)).stem, body=body, source=source))
        return templates

    def _local_templates(self) -> list[PrTemplate]:
        root = self.repo_root
        candidates: list[Path] = []
        single = root / ".github" / "pull_request_template.md"
        if single.is_file():
            candidates.append(single)
        directory = root / ".github" / "PULL_REQUEST_TEMPLATE"
        if directory.is_dir():
            candidates.extend(sorted(directory.glob("*.md")))
        templates: list[PrTemplate] = []
        for path in candidates:
            templates.append(
                PrTemplate(
                    name=path.stem,
                    body=path.read_text(encoding="utf-8"),
                    source=f"local:{path.relative_to(root).as_posix()}",
                )
            )
        return templates

    def _needs_push(self, plan: GitPushPlan) -> bool:
        if plan.create_branch_first or plan.dirty:
            return True
        if plan.remote is None:
            return True
        try:
            head = self.git.rev_parse("HEAD")
            return not self.git.commit_on_remote_branch(plan.remote, plan.target_branch, head)
        except Exception:
            return True
