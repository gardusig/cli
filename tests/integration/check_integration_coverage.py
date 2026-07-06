#!/usr/bin/env python3
"""Fast gate: every public CLI command has ok + fail integration checks registered."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.integration.integration_coverage import (  # noqa: E402
    assert_integration_coverage_gate,
    format_integration_coverage_report,
    integration_coverage_summary,
    manifest_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print human-readable inventory of tested commands.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON manifest (for CI artifacts and external tooling).",
    )
    args = parser.parse_args()

    if args.json:
        print(manifest_json())
        return 0
    if args.list:
        print(format_integration_coverage_report())
        return 0

    assert_integration_coverage_gate()
    summary = integration_coverage_summary()
    print(
        "Integration coverage gate passed "
        f"({summary['complete']}/{summary['total_commands']} commands, "
        f"api/git/pypi/docker/contest/project/top)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
