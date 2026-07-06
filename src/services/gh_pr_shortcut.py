"""One-shot GitHub PR shortcut orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.services.gh_service import GhService
from src.services.git_shortcuts import GitPushPlan, GitPushResult, GitShortcuts


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
        data = self.gh.pr_create(title=plan.title, body=plan.body)
        data["pushed"] = bool(push_result and push_result.pushed)
        data["branch"] = push_result.branch if push_result else plan.branch
        data["body_source"] = plan.body_source
        return data

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
        if plan.create_branch_first or plan.dirty or plan.remote is None:
            return True
        try:
            head = self.git.rev_parse("HEAD")
            return not self.git.commit_on_remote_branch(plan.remote, plan.target_branch, head)
        except Exception:
            return True
