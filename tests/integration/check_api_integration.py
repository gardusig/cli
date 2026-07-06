#!/usr/bin/env python3
"""Run all API docker integration tests (isolated fixtures, mocked remotes)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _run_full_api_integration() -> int:
    from src.integration.workspaces import INTEGRATION_TEST_MODULES

    args = [sys.executable, "-m", "pytest", "-q", "--no-cov"]
    for mod in INTEGRATION_TEST_MODULES:
        path = mod.replace(".", "/") + ".py"
        args.append(path)

    result = subprocess.run(args, cwd=ROOT, check=False)
    return result.returncode


def _run_package_api_integration(package: str) -> int:
    from src.integration.docker_guard import require_docker_integration
    from src.integration.package_integration import run_package_integration

    require_docker_integration(context=f"check_api_integration.py --package {package}")
    errors = run_package_integration(package, ROOT)
    if errors:
        print(f"API package integration failed ({package}):", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
            print("---", file=sys.stderr)
        return 1
    print(f"API package integration passed ({package}).")
    return 0


def main() -> int:
    from src.integration.package_integration import runner_packages

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package",
        choices=sorted(runner_packages()),
        help="Run only one API-backed CLI package integration leg.",
    )
    args = parser.parse_args()
    if args.package:
        return _run_package_api_integration(args.package)
    return _run_full_api_integration()


if __name__ == "__main__":
    raise SystemExit(main())
