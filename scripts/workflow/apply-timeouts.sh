#!/usr/bin/env bash
# Apply scripts/workflow/workflow-step-tiers.yaml to .github/workflows/*.yaml
#   --check  verify only (no writes)
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$root"
exec python3 - "$@" <<'PY'
"""Apply tiered step timeouts and job totals to GitHub Actions workflow YAML."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(".")
SCRIPT_DIR = ROOT / "scripts" / "workflow"
TIERS_FILE = SCRIPT_DIR / "timeout-tiers.yaml"
STEPS_FILE = SCRIPT_DIR / "workflow-step-tiers.yaml"
WORKFLOWS_DIR = ROOT / ".github" / "workflows"


def _load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _load_workflow(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    patched = re.sub(r"^on:", "_on:", text, count=1, flags=re.MULTILINE)
    data = yaml.safe_load(patched)
    if not isinstance(data, dict):
        raise SystemExit(f"invalid workflow: {path}")
    if "_on" in data:
        data["on"] = data.pop("_on")
    return data


def _tier_minutes(tiers: dict[str, int], label: str) -> int:
    if label not in tiers:
        raise SystemExit(f"unknown tier {label!r}; expected short, medium, or long")
    minutes = int(tiers[label])
    if minutes not in {3, 6, 9}:
        raise SystemExit(f"tier {label!r} must map to 3, 6, or 9 minutes (got {minutes})")
    return minutes


def _step_ids(steps: list[dict[str, Any]]) -> list[str]:
    ids: list[str] = []
    for step in steps:
        step_id = step.get("id")
        if not step_id:
            raise SystemExit(f"step missing id: {step!r}")
        ids.append(str(step_id))
    return ids


def _set_step_timeout(lines: list[str], step_id: str, minutes: int) -> bool:
    step_re = re.compile(rf"^(\s*)- id: {re.escape(step_id)}\s*$")
    timeout_re = re.compile(r"^(\s*)timeout-minutes:\s*\d+\s*$")
    changed = False
    i = 0
    while i < len(lines):
        match = step_re.match(lines[i])
        if not match:
            i += 1
            continue
        indent = match.group(1)
        step_indent = indent + "  "
        j = i + 1
        timeout_idx: int | None = None
        last_prop = i
        while j < len(lines):
            line = lines[j]
            if line.startswith(indent + "- ") and j != i:
                break
            if line.startswith(step_indent) or line.strip() == "":
                if timeout_re.match(line):
                    timeout_idx = j
                if line.strip() and not line.lstrip().startswith("#"):
                    last_prop = j
                j += 1
                continue
            break
        new_line = f"{step_indent}timeout-minutes: {minutes}"
        if timeout_idx is not None:
            if lines[timeout_idx] != new_line:
                lines[timeout_idx] = new_line
                changed = True
        else:
            lines.insert(last_prop + 1, new_line)
            changed = True
        i = j
    return changed


def _set_job_timeout(lines: list[str], job_id: str, minutes: int) -> bool:
    job_re = re.compile(rf"^  {re.escape(job_id)}:\s*$")
    timeout_re = re.compile(r"^    timeout-minutes:\s*\d+\s*$")
    changed = False
    i = 0
    while i < len(lines):
        if not job_re.match(lines[i]):
            i += 1
            continue
        j = i + 1
        timeout_idx: int | None = None
        insert_after = i
        while j < len(lines):
            line = lines[j]
            if re.match(r"^  [A-Za-z0-9_-]+:\s*$", line):
                break
            if timeout_re.match(line):
                timeout_idx = j
            if line.startswith("    ") and line.strip():
                insert_after = j
            j += 1
        new_line = f"    timeout-minutes: {minutes}"
        if timeout_idx is not None:
            if lines[timeout_idx] != new_line:
                lines[timeout_idx] = new_line
                changed = True
        else:
            lines.insert(insert_after + 1, new_line)
            changed = True
        i = j
    return changed


def _apply_workflow(
    workflow_path: Path,
    job_tiers: dict[str, dict[str, str]],
    tiers: dict[str, int],
    *,
    check: bool,
) -> list[str]:
    data = _load_workflow(workflow_path)
    jobs = data.get("jobs") or {}
    errors: list[str] = []
    workflow_name = workflow_path.name

    if set(jobs) != set(job_tiers):
        errors.append(
            f"{workflow_name}: job keys mismatch "
            f"(workflow={sorted(jobs)}, config={sorted(job_tiers)})"
        )
        return errors

    expected_job_totals: dict[str, int] = {}
    expected_step_timeouts: dict[str, dict[str, int]] = {}

    for job_id, job in jobs.items():
        expected = job_tiers[job_id]
        steps = job.get("steps") or []
        step_ids = _step_ids(steps)
        if set(step_ids) != set(expected):
            errors.append(
                f"{workflow_name} job {job_id}: step id mismatch "
                f"(workflow={step_ids}, config={sorted(expected)})"
            )
            continue

        total = 0
        step_timeouts: dict[str, int] = {}
        for step in steps:
            step_id = str(step["id"])
            tier = expected[step_id]
            minutes = _tier_minutes(tiers, tier)
            total += minutes
            step_timeouts[step_id] = minutes
            current = step.get("timeout-minutes")
            if current != minutes:
                errors.append(
                    f"{workflow_name} job {job_id} step {step_id}: "
                    f"timeout-minutes={current!r} expected {minutes} ({tier})"
                )

        expected_step_timeouts[job_id] = step_timeouts
        expected_job_totals[job_id] = total
        job_total = job.get("timeout-minutes")
        if job_total != total:
            errors.append(
                f"{workflow_name} job {job_id}: "
                f"timeout-minutes={job_total!r} expected sum {total}"
            )

    if check or errors:
        return errors

    lines = workflow_path.read_text(encoding="utf-8").splitlines()
    changed = False
    for job_id, step_timeouts in expected_step_timeouts.items():
        for step_id, minutes in step_timeouts.items():
            changed = _set_step_timeout(lines, step_id, minutes) or changed
        changed = _set_job_timeout(lines, job_id, expected_job_totals[job_id]) or changed

    if changed:
        workflow_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify workflows match tier config without writing",
    )
    args = parser.parse_args(argv)

    tiers = {k: int(v) for k, v in _load_yaml(TIERS_FILE).items()}
    step_config = _load_yaml(STEPS_FILE)

    all_errors: list[str] = []
    for workflow_name, job_tiers in step_config.items():
        path = WORKFLOWS_DIR / workflow_name
        if not path.is_file():
            all_errors.append(f"missing workflow: {path}")
            continue
        all_errors.extend(
            _apply_workflow(path, job_tiers, tiers, check=args.check)
        )

    if all_errors:
        for line in all_errors:
            print(line, file=sys.stderr)
        return 1

    if args.check:
        print("workflow timeouts match tier config")
    else:
        print("applied workflow step tiers and job timeout sums")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY
