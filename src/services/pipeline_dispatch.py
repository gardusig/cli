"""Dispatch gardusig/github-pipelines repository_dispatch events."""

from __future__ import annotations

import json
import subprocess
from typing import Any

HUB_REPOSITORY = "gardusig/github-pipelines"


def dispatch_repository_event(
    event_type: str,
    client_payload: dict[str, Any],
    *,
    dry_run: bool = False,
    hub_repository: str = HUB_REPOSITORY,
) -> dict[str, Any]:
    """POST a repository_dispatch event to the hub pipelines repo."""
    envelope = {"event_type": event_type, "client_payload": client_payload}
    if dry_run:
        return envelope
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
