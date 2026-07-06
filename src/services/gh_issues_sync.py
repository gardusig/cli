"""Sync local task pairs with GitHub Issues."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from src.models.task import TaskMetadata, TaskPair
from src.services.gh_service import GhService
from src.services.notion_pairs import _read_task_body, dump_header, load_header, load_pairs, slugify
from src.services.notion_sync import build_pairs_manifest
from src.utils.config import (
    gh_issues_closed_older_than,
    gh_issues_labels_manifest,
    gh_issues_repo,
    notion_pairs_file,
    notion_task_root,
)


@dataclass
class IssueSyncResult:
    deleted: list[int] = field(default_factory=list)
    created: list[dict[str, Any]] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _labels(meta: TaskMetadata) -> list[str]:
    labels = list(dict.fromkeys(meta.labels or []))
    if "issue-type:task" not in labels:
        labels.append("issue-type:task")
    if meta.priority is not None:
        labels.append(f"priority:{meta.priority}")
    if meta.tag:
        labels.append(f"area:{meta.tag}")
    return list(dict.fromkeys(labels))


def _ensure_database_repo(repo: str) -> None:
    if os.environ.get("CLI_GH_ISSUES_DEPLOY_ALLOW") == "1":
        return
    if repo.split("/")[-1] != "database":
        raise RuntimeError("GitHub issue sync is restricted to repositories named 'database'.")


def deploy_issues(*, svc: GhService | None = None, dry_run: bool = False) -> IssueSyncResult:
    repo = gh_issues_repo()
    _ensure_database_repo(repo)
    svc = svc or GhService(repo=repo)
    root = notion_task_root()
    pairs = load_pairs(notion_pairs_file(), task_root=root)
    result = IssueSyncResult()

    for pair in pairs:
        meta = load_header(pair.header_path(root))
        if not meta.enabled:
            result.skipped.append(meta.name)

    existing = svc.issue_list_all(state="all", limit=500)
    if dry_run:
        result.deleted = [int(row["number"]) for row in existing]
        for pair in pairs:
            meta = load_header(pair.header_path(root))
            if meta.enabled:
                result.created.append({"title": meta.name, "labels": _labels(meta)})
        return result

    labels_manifest = gh_issues_labels_manifest()
    if labels_manifest.is_file():
        svc.label_sync(labels_manifest)

    for row in existing:
        number = int(row["number"])
        svc.issue_delete(number)
        result.deleted.append(number)

    for pair in pairs:
        meta = load_header(pair.header_path(root))
        if not meta.enabled:
            continue
        body = _read_task_body(pair.body_path(root))
        result.created.append(svc.issue_create(title=meta.name, body=body, labels=_labels(meta)))
    return result


def ingest_issues(*, svc: GhService | None = None) -> IssueSyncResult:
    repo = gh_issues_repo()
    _ensure_database_repo(repo)
    svc = svc or GhService(repo=repo)
    root = notion_task_root()
    existing_pairs = {
        load_header(pair.header_path(root)).name: pair
        for pair in load_pairs(notion_pairs_file(), task_root=root)
        if pair.header_path(root).is_file()
    }
    result = IssueSyncResult()
    for issue in svc.issue_list_all(state="open", limit=500, fields="number,title,body,labels,state,url"):
        title = str(issue["title"])
        pair = existing_pairs.get(title)
        if pair is None:
            slug = slugify(title)
            pair = TaskPair(header_filepath=f"header/{slug}.yaml", body_filepath=f"body/{slug}.yaml")
        labels = [
            str(label.get("name", label)) if isinstance(label, dict) else str(label)
            for label in issue.get("labels", [])
        ]
        header = pair.header_path(root)
        body = pair.body_path(root)
        if header.is_file():
            meta = load_header(header)
            meta.name = title
            meta.labels = labels
        else:
            meta = TaskMetadata(name=title, labels=labels)
        dump_header(header, meta)
        body.parent.mkdir(parents=True, exist_ok=True)
        body.write_text(
            yaml.safe_dump(
                {
                    "format": "markdown",
                    "wiki_filepath": "",
                    "body": str(issue.get("body") or ""),
                },
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        result.created.append({"title": title, "number": issue.get("number")})
    build_pairs_manifest(root)
    return result


def _parse_duration(value: str) -> timedelta:
    stripped = value.strip().lower()
    if stripped.endswith("w"):
        return timedelta(weeks=int(stripped[:-1]))
    if stripped.endswith("d"):
        return timedelta(days=int(stripped[:-1]))
    return timedelta(days=int(stripped))


def prune_issues(
    *,
    svc: GhService | None = None,
    closed_older_than: str | None = None,
    include_labels: list[str] | None = None,
    exclude_labels: list[str] | None = None,
    dry_run: bool = False,
) -> IssueSyncResult:
    repo = gh_issues_repo()
    _ensure_database_repo(repo)
    svc = svc or GhService(repo=repo)
    age = _parse_duration(closed_older_than or gh_issues_closed_older_than())
    cutoff = datetime.now(UTC) - age
    include = set(include_labels or [])
    exclude = set(exclude_labels or [])
    result = IssueSyncResult()
    for issue in svc.issue_list_all(state="closed", limit=500):
        raw_closed = issue.get("closedAt")
        if not raw_closed:
            continue
        closed_at = datetime.fromisoformat(str(raw_closed).replace("Z", "+00:00"))
        labels = {
            str(label.get("name", label)) if isinstance(label, dict) else str(label)
            for label in issue.get("labels", [])
        }
        if closed_at >= cutoff:
            continue
        if include and not include.issubset(labels):
            continue
        if exclude and exclude.intersection(labels):
            continue
        number = int(issue["number"])
        result.deleted.append(number)
        if not dry_run:
            svc.issue_delete(number)
    return result
