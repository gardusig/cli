"""Smoke-script integration gate (replaces per-command inventory)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.integration.integration_coverage import assert_integration_coverage_gate

ROOT = Path(__file__).resolve().parents[2]
CHECK_SCRIPT = ROOT / "tests" / "integration" / "check_integration_coverage.py"
SMOKE = ROOT / "scripts" / "pull-request" / "integration-smoke.sh"


def test_integration_coverage_gate_passes() -> None:
    assert_integration_coverage_gate()


def test_integration_smoke_script_exists() -> None:
    assert SMOKE.is_file()


def test_check_integration_coverage_script_gate() -> None:
    result = subprocess.run(
        [sys.executable, str(CHECK_SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "Integration coverage gate passed" in result.stdout


def test_check_integration_coverage_script_json() -> None:
    result = subprocess.run(
        [sys.executable, str(CHECK_SCRIPT), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["mode"] == "smoke"
    assert data["summary"]["incomplete"] == 0
