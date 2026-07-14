#!/usr/bin/env bash
# Print per-job timeout sums from workflow-step-tiers.yaml (tier minutes only).
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$root"
python3 - <<'PY'
import yaml
from pathlib import Path

root = Path(".")
tiers = yaml.safe_load((root / "scripts/workflow/timeout-tiers.yaml").read_text())
steps = yaml.safe_load((root / "scripts/workflow/workflow-step-tiers.yaml").read_text())

for workflow, jobs in steps.items():
    print(f"== {workflow} ==")
    for job_id, step_tiers in jobs.items():
        total = sum(int(tiers[tier]) for tier in step_tiers.values())
        detail = " + ".join(
            f"{step}({tiers[tier]}m)" for step, tier in step_tiers.items()
        )
        print(f"  {job_id}: {total}m  [{detail}]")
PY
