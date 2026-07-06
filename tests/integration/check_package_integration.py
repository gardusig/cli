#!/usr/bin/env python3
"""Run integration checks for a single CLI package (selective CI leg)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.integration.docker_guard import require_docker_integration  # noqa: E402
from src.integration.package_integration import (  # noqa: E402
    runner_packages,
    run_package_integration,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package",
        required=True,
        choices=sorted(runner_packages()),
        help="CLI package name from test_packages registry",
    )
    args = parser.parse_args()

    require_docker_integration(context=f"check_package_integration.py --package {args.package}")
    errors = run_package_integration(args.package, ROOT)
    if errors:
        print(f"Package integration failed ({args.package}):", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
            print("---", file=sys.stderr)
        return 1
    print(f"Package integration passed ({args.package}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
