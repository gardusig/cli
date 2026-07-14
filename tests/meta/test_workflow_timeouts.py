"""Workflow timeout tier config and apply script."""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from tests.constants import ROOT

TIERS = ROOT / "scripts" / "workflow" / "timeout-tiers.yaml"
STEPS = ROOT / "scripts" / "workflow" / "workflow-step-tiers.yaml"
APPLY = ROOT / "scripts" / "workflow" / "apply-timeouts.sh"


def test_timeout_tiers_are_3_6_9() -> None:
    tiers = yaml.safe_load(TIERS.read_text(encoding="utf-8"))
    assert tiers == {"short": 3, "medium": 6, "long": 9}


def test_workflow_timeouts_match_tier_config() -> None:
    result = subprocess.run(
        ["bash", str(APPLY), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_workflows_orchestrate_docker_only() -> None:
    workflows = ROOT / ".github" / "workflows"
    for path in sorted(workflows.glob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        assert "bash scripts/" not in text, path.name
        assert ".sh" not in text, path.name
        assert "scripts/" not in text, path.name
        assert "docker build" in text, path.name


def test_job_timeout_sums_match_step_tiers() -> None:
    tiers = yaml.safe_load(TIERS.read_text(encoding="utf-8"))
    step_config = yaml.safe_load(STEPS.read_text(encoding="utf-8"))
    for workflow_name, jobs in step_config.items():
        workflow = yaml.safe_load(
            (ROOT / ".github" / "workflows" / workflow_name)
            .read_text(encoding="utf-8")
            .replace("\non:", "\n_on:", 1)
        )
        if "_on" in workflow:
            workflow["on"] = workflow.pop("_on")
        for job_id, step_tiers in jobs.items():
            job = workflow["jobs"][job_id]
            expected = sum(int(tiers[tier]) for tier in step_tiers.values())
            assert job["timeout-minutes"] == expected, job_id
