"""GitHub issue/label/PR services via gh provider."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

from src.providers.gh import GhProvider
from src.services.gh_policy import MergeForbiddenError
from src.services.gh_sequence import SequenceKey
from src.services.gh_topo import StepKey, build_parent_child_tree, load_priority_levels, pick_next_child, sort_children


class GhService:
    def __init__(self, *, repo: str | None = None) -> None:
        self.provider = GhProvider(repo=repo)

    def repo_display(self) -> str:
        return self.provider.repo or self.provider.default_repo()

    # --- Issue read ---

    def issue_list(
        self,
        *,
        state: str = "open",
        label: list[str] | None = None,
        limit: int = 30,
        fields: str = "number,title,state,labels,url,closedAt",
    ) -> list[dict[str, Any]]:
        args = [
            "issue",
            "list",
            "--state",
            state,
            "--limit",
            str(limit),
            "--json",
            fields,
        ]
        for lb in label or []:
            args.extend(["--label", lb])
        return self.provider.run_json(args)

    def issue_list_all(
        self,
        *,
        state: str = "open",
        label: list[str] | None = None,
        limit: int = 500,
        fields: str = "number,title,state,labels,url,closedAt",
    ) -> list[dict[str, Any]]:
        # `gh issue list` is not offset-based. Use a high cap and keep the cap explicit.
        return self.issue_list(state=state, label=label, limit=limit, fields=fields)

    def issue_view(self, number: int, *, comments: bool = False) -> dict[str, Any]:
        fields = "number,title,body,state,labels,url,author,createdAt,updatedAt"
        args = ["issue", "view", str(number), "--json", fields]
        if comments:
            args.append("--comments")
        return self.provider.run_json(args)

    def issue_context(self, number: int) -> dict[str, Any]:
        """Full issue rollup: view, comments, epic parent, siblings, body-linked issues."""
        raw = self.issue_view(number, comments=True)
        comments = raw.pop("comments", [])
        labels = [
            str(lb.get("name", lb)) if isinstance(lb, dict) else str(lb)
            for lb in raw.get("labels", [])
        ]
        epic_label = next((lb for lb in labels if lb.startswith("epic:")), None)
        epic_info: dict[str, Any] | None = None
        siblings: list[dict[str, Any]] = []
        if epic_label:
            all_issues = self.issue_list(state="open", limit=200)
            epic_parent: dict[str, Any] | None = None
            for row in all_issues:
                row_labels = [
                    str(lb.get("name", lb)) if isinstance(lb, dict) else str(lb)
                    for lb in row.get("labels", [])
                ]
                if epic_label in row_labels and "issue-type:epic" in row_labels:
                    epic_parent = {"number": row["number"], "title": row["title"]}
                    break
            for row in all_issues:
                row_labels = [
                    str(lb.get("name", lb)) if isinstance(lb, dict) else str(lb)
                    for lb in row.get("labels", [])
                ]
                if (
                    epic_label in row_labels
                    and "issue-type:child" in row_labels
                    and int(row["number"]) != number
                ):
                    siblings.append({"number": row["number"], "title": row["title"]})
            epic_info = {"slug": epic_label, "parent": epic_parent}
        linked: list[dict[str, Any]] = []
        body = str(raw.get("body", ""))
        seen: set[int] = set()
        for match in re.finditer(r"#(\d+)", body):
            ref_num = int(match.group(1))
            if ref_num == number or ref_num in seen:
                continue
            seen.add(ref_num)
            try:
                ref = self.issue_view(ref_num)
            except Exception:
                continue
            linked.append(
                {"number": ref_num, "title": ref["title"], "relation": "body_ref"}
            )
        return {
            "issue": raw,
            "comments": comments,
            "epic": epic_info,
            "siblings": siblings,
            "linked_issues": linked,
            "labels": labels,
        }

    def issue_search(self, query: str, *, limit: int = 30) -> list[dict[str, Any]]:
        args = [
            "search",
            "issues",
            query,
            "--limit",
            str(limit),
            "--json",
            "number,title,state,labels,url",
        ]
        return self.provider.run_json(args)

    # --- Issue write ---

    def issue_create(
        self,
        *,
        title: str,
        body_file: Path | None = None,
        body: str | None = None,
        labels: list[str] | None = None,
    ) -> dict[str, Any]:
        args = ["issue", "create", "--title", title]
        if body_file:
            args.extend(["--body-file", str(body_file)])
        elif body:
            args.extend(["--body", body])
        if labels:
            args.extend(["--label", ",".join(labels)])
        url = self.provider.run(args)
        number = int(url.rstrip("/").split("/")[-1])
        return {"url": url, "number": number, "title": title}

    def issue_edit(
        self,
        number: int,
        *,
        title: str | None = None,
        body_file: Path | None = None,
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
    ) -> None:
        args = ["issue", "edit", str(number)]
        if title:
            args.extend(["--title", title])
        if body_file:
            args.extend(["--body-file", str(body_file)])
        for lb in add_labels or []:
            args.extend(["--add-label", lb])
        for lb in remove_labels or []:
            args.extend(["--remove-label", lb])
        self.provider.run(args)

    def issue_close(self, number: int, *, comment: str | None = None) -> None:
        args = ["issue", "close", str(number)]
        if comment:
            args.extend(["--comment", comment])
        self.provider.run(args)

    def issue_delete(self, number: int) -> None:
        self.provider.run(["issue", "delete", str(number), "--yes"])

    def issue_comment(self, number: int, *, body: str) -> None:
        self.provider.run(["issue", "comment", str(number), "--body", body])

    def issue_batch(self, batch_file: Path) -> list[dict[str, Any]]:
        data = yaml.safe_load(batch_file.read_text(encoding="utf-8"))
        ops = data.get("operations") or data.get("issues") or []
        results: list[dict[str, Any]] = []
        for op in ops:
            kind = op.get("action") or op.get("kind") or "create"
            if kind == "create":
                results.append(
                    self.issue_create(
                        title=op["title"],
                        body_file=Path(op["body_file"]) if op.get("body_file") else None,
                        body=op.get("body"),
                        labels=op.get("labels"),
                    )
                )
            elif kind == "edit":
                self.issue_edit(
                    int(op["number"]),
                    title=op.get("title"),
                    body_file=Path(op["body_file"]) if op.get("body_file") else None,
                    add_labels=op.get("add_labels"),
                    remove_labels=op.get("remove_labels"),
                )
                results.append({"number": op["number"], "action": "edit"})
            elif kind == "close":
                raise ValueError(
                    "issue close is blocked by policy; merge a PR in the GitHub UI "
                    "and let linked issues auto-close"
                )
            else:
                raise ValueError(f"Unknown batch action: {kind}")
        return results

    # --- Labels ---

    def label_list(self) -> list[dict[str, Any]]:
        return self.provider.run_json(["label", "list", "--json", "name,color,description"])

    def label_create(self, name: str, *, color: str = "ededed", description: str = "") -> None:
        args = ["label", "create", name, "--color", color]
        if description:
            args.extend(["--description", description])
        self.provider.run(args)

    def label_delete(self, name: str) -> None:
        self.provider.run(["label", "delete", name, "--yes"])

    def label_sync(
        self,
        manifest_path: Path,
        *,
        prune_orphans: bool = False,
    ) -> dict[str, Any]:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        desired = {entry["name"]: entry for entry in manifest.get("labels", [])}
        existing = {lb["name"]: lb for lb in self.label_list()}
        created: list[str] = []
        for name, spec in desired.items():
            if name not in existing:
                self.label_create(
                    name,
                    color=spec.get("color", "ededed"),
                    description=spec.get("description", ""),
                )
                created.append(name)
        deleted: list[str] = []
        if prune_orphans:
            protected = set(manifest.get("protected", []))
            for name in existing:
                if name not in desired and name not in protected:
                    self.label_delete(name)
                    deleted.append(name)
        return {"created": created, "deleted": deleted, "manifest": str(manifest_path)}

    # --- PR ---

    def pr_list(
        self,
        *,
        state: str = "open",
        limit: int = 30,
        head: str | None = None,
        base: str | None = None,
    ) -> list[dict[str, Any]]:
        args = [
            "pr",
            "list",
            "--state",
            state,
            "--limit",
            str(limit),
            "--json",
            "number,title,state,url,headRefName,baseRefName,mergedAt",
        ]
        if head:
            args.extend(["--head", head])
        if base:
            args.extend(["--base", base])
        return self.provider.run_json(args)

    def repo_list(
        self,
        *,
        owner: str,
        limit: int = 100,
        visibility: str | None = "public",
        fields: str = "name,description,visibility,url",
    ) -> list[dict[str, Any]]:
        args = [
            "repo",
            "list",
            "--owner",
            owner,
            "--limit",
            str(limit),
            "--json",
            fields,
        ]
        if visibility:
            args.extend(["--visibility", visibility])
        rows = self.provider.run_json(args)
        return sorted(rows, key=lambda row: str(row.get("name", "")).lower())

    def repo_view(
        self,
        *,
        fields: str = "nameWithOwner,owner,issueTemplates,pullRequestTemplates",
    ) -> dict[str, Any]:
        return self.provider.run_json(["repo", "view", "--json", fields])

    def pr_view(self, number: int) -> dict[str, Any]:
        return self.provider.run_json(
            [
                "pr",
                "view",
                str(number),
                "--json",
                "number,title,body,state,url,headRefName,baseRefName,commits,files",
            ]
        )

    def pr_diff(self, number: int) -> str:
        return self.provider.run(["pr", "diff", str(number)])

    def pr_diff_stat(self, number: int) -> str:
        return self.provider.run(["pr", "diff", str(number), "--stat"])

    def pr_create(
        self,
        *,
        title: str,
        body_file: Path | None = None,
        body: str | None = None,
        base: str | None = None,
        head: str | None = None,
    ) -> dict[str, Any]:
        args = ["pr", "create", "--title", title]
        if body_file:
            args.extend(["--body-file", str(body_file)])
        elif body:
            args.extend(["--body", body])
        if base:
            args.extend(["--base", base])
        if head:
            args.extend(["--head", head])
        url = self.provider.run(args)
        number = int(url.rstrip("/").split("/")[-1])
        return {"url": url, "number": number, "title": title}

    def pr_edit(
        self,
        number: int,
        *,
        title: str | None = None,
        body_file: Path | None = None,
    ) -> None:
        args = ["pr", "edit", str(number)]
        if title:
            args.extend(["--title", title])
        if body_file:
            args.extend(["--body-file", str(body_file)])
        self.provider.run(args)

    def pr_comment(self, number: int, *, body: str) -> None:
        self.provider.run(["pr", "comment", str(number), "--body", body])

    def pr_close(self, number: int) -> None:
        self.provider.run(["pr", "close", str(number)])

    def pr_merge(
        self,
        number: int,
        *,
        merge_method: str = "merge",
        delete_branch: bool = False,
    ) -> None:
        raise MergeForbiddenError()

    # --- Backlog ---

    def backlog_tree(self) -> dict[str, Any]:
        open_issues = self.issue_list(state="open", limit=200)
        closed_issues = self.issue_list(state="closed", limit=100)
        seen: set[int] = set()
        merged: list[dict[str, Any]] = []
        for issue in open_issues + closed_issues:
            number = int(issue.get("number", 0))
            if number in seen:
                continue
            seen.add(number)
            merged.append(issue)
        for issue in merged:
            labels = issue.get("labels", [])
            issue["labels"] = [
                lb.get("name", lb) if isinstance(lb, dict) else lb for lb in labels
            ]
        organized = build_parent_child_tree(merged)
        return {
            "repo": self.repo_display(),
            **organized,
            # legacy flat keys for older consumers
            "roots": [p for p in organized["parents"]],
            "epics": {
                (p.get("epic") or f"_parent_{p['number']}"): p.get("children", [])
                for p in organized["parents"]
            },
        }

    def backlog_organize(self) -> dict[str, Any]:
        """Parent/child tree with priority level explanations and readiness."""
        return self.backlog_tree()

    def backlog_next(self) -> dict[str, Any] | None:
        open_issues = self.issue_list(state="open", limit=200)
        closed_issues = self.issue_list(state="closed", limit=200)
        all_issues = open_issues + closed_issues
        for issue in all_issues:
            labels = issue.get("labels", [])
            issue["labels"] = [
                lb.get("name", lb) if isinstance(lb, dict) else lb for lb in labels
            ]
        picked = pick_next_child(all_issues)
        if picked:
            return picked
        candidate = sort_children(open_issues)
        if not candidate:
            return None
        first = candidate[0]
        step = StepKey.from_title(str(first.get("title", "")))
        return {
            "number": first["number"],
            "title": first["title"],
            "url": first.get("url"),
            "step": step.step if step else None,
        }

    def backlog_resequence(self, plan_file: Path) -> list[dict[str, Any]]:
        plan = yaml.safe_load(plan_file.read_text(encoding="utf-8"))
        results: list[dict[str, Any]] = []
        for entry in plan.get("renames", []):
            number = int(entry["number"])
            new_title = entry["title"]
            self.issue_edit(number, title=new_title)
            results.append({"number": number, "title": new_title})
        return results

    def snapshot_summary(self) -> list[str]:
        return [f"repo: {self.repo_display()}"]
