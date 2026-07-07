"""Dispatch gardusig/github-pipelines repository_dispatch events."""

from __future__ import annotations

import json
import subprocess
from typing import Any

HUB_REPOSITORY = "gardusig/pipelines"
_ACTIVE_RUN_STATUSES = frozenset({"in_progress", "queued", "pending", "waiting"})


def list_active_hub_runs(
    *,
    hub_repository: str = HUB_REPOSITORY,
    display_title: str | None = None,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """Return in-flight workflow runs on the hub (newest first)."""
    proc = subprocess.run(
        [
            "gh",
            "run",
            "list",
            "--repo",
            hub_repository,
            "--limit",
            str(limit),
            "--json",
            "databaseId,status,displayTitle,createdAt,url",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    runs = json.loads(proc.stdout or "[]")
    active: list[dict[str, Any]] = []
    for run in runs:
        if run.get("status") not in _ACTIVE_RUN_STATUSES:
            continue
        if display_title is not None and run.get("displayTitle") != display_title:
            continue
        active.append(run)
    return active


def dispatch_repository_event(
    event_type: str,
    client_payload: dict[str, Any],
    *,
    dry_run: bool = False,
    force: bool = False,
    hub_repository: str = HUB_REPOSITORY,
) -> dict[str, Any]:
    """POST a repository_dispatch event to the hub pipelines repo."""
    envelope = {"event_type": event_type, "client_payload": client_payload}
    if dry_run:
        return envelope
    if not force and event_type == "pull-request":
        active = list_active_hub_runs(hub_repository=hub_repository, display_title="pull-request")
        if active:
            newest = active[0]
            raise SystemExit(
                "hub already has "
                f"{len(active)} active pull-request run(s); "
                f"cancel stale runs before redispatching. "
                f"Latest: {newest.get('url', newest.get('databaseId'))}. "
                "Pass --force to dispatch anyway."
            )
    body = json.dumps(envelope)
    subprocess.run(
        [
            "gh",
            "api",
            "--method",
            "POST",
            f"repos/{hub_repository}/dispatches",
            "--input",
            "-",
        ],
        input=body,
        text=True,
        check=True,
    )
    return {"dispatched": True, **envelope}
