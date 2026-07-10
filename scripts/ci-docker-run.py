#!/usr/bin/env python3
"""Run one hub Docker pipeline job (was `cli pipeline docker run`)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ci_runtime.runtime import run_docker_job


def main() -> None:
    parser = argparse.ArgumentParser(prog="scripts/ci-docker-run.py")
    parser.add_argument("--job-json", required=True)
    parser.add_argument("--pipeline-src", type=Path, required=True)
    parser.add_argument("--app-src", type=Path, required=True)
    parser.add_argument("--tag-prefix", default="pipeline")
    parser.add_argument("--release-version", default="")
    parser.add_argument("--pages-output", type=Path, default=Path("publish-pages"))
    args = parser.parse_args()
    run_docker_job(args)


if __name__ == "__main__":
    main()
