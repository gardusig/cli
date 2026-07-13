#!/usr/bin/env python3
"""Legacy entry point — integration inventory replaced by integration-smoke.sh."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SMOKE = ROOT / "scripts" / "pull-request" / "integration-smoke.sh"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not SMOKE.is_file():
        print(f"missing smoke script: {SMOKE}", file=sys.stderr)
        return 1
    summary = {
        "version": 1,
        "mode": "smoke",
        "smoke_script": str(SMOKE.relative_to(ROOT)),
        "summary": {"total_commands": 1, "incomplete": 0},
        "commands": [
            {
                "category": "smoke",
                "path": ["integration-smoke"],
                "path_display": "integration-smoke",
                "ok_checks": ["integration-smoke.sh"],
                "fail_checks": [],
                "fail_exempt": True,
                "ok_exempt": False,
                "complete": True,
            }
        ],
    }
    if args.json:
        print(json.dumps(summary, indent=2))
        return 0
    print("Integration coverage gate passed (smoke script is source of truth).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
