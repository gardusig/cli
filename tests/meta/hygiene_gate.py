#!/usr/bin/env python3
"""Repo hygiene gate for scripts/ci/repo-hygiene.sh (no Typer/cli entry)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.repo_hygiene import (  # noqa: E402
    HygienePolicy,
    check_repo_hygiene,
    load_hygiene_policy,
    policy_with_ignored_paths,
)


def _policy_from_json(raw: str) -> HygienePolicy | None:
    data: dict[str, Any] = json.loads(raw)
    policy = HygienePolicy.from_mapping(data)
    ignored = data.get("ignored_prefixes") or []
    if ignored:
        return policy_with_ignored_paths(policy, tuple(ignored))
    return policy


def main() -> int:
    policy: HygienePolicy | None = None
    raw = os.environ.get("HYGIENE_POLICY_JSON", "").strip()
    if raw:
        policy = _policy_from_json(raw)
    policy_path = os.environ.get("POLICY_FILE", "").strip()
    if policy_path:
        policy = load_hygiene_policy(Path(policy_path))
    errors = check_repo_hygiene(
        ROOT,
        policy=policy,
        require_structure=True,
    )
    if errors:
        print("structure failed:", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print("structure ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
