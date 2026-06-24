"""Gate: every public CLI command is listed with ok + fail integration checks."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from cli.integration.integration_coverage import (
    assert_integration_coverage_gate,
    integration_coverage_inventory,
    integration_coverage_manifest,
    integration_coverage_summary,
)

ROOT = Path(__file__).resolve().parents[1]
CHECK_SCRIPT = ROOT / "tests" / "integration" / "check_integration_coverage.py"


def test_integration_coverage_gate_passes() -> None:
    assert_integration_coverage_gate()


def test_every_inventory_row_has_ok_and_fail_checks() -> None:
    for row in integration_coverage_inventory():
        assert row.ok_checks, f"{row.path_display}: missing ok checks"
        if row.fail_exempt:
            continue
        assert row.fail_checks, f"{row.path_display}: missing fail checks"


def test_manifest_lists_all_categories() -> None:
    manifest = integration_coverage_manifest()
    assert manifest["version"] == 1
    assert manifest["summary"]["total_commands"] > 0
    assert manifest["summary"]["incomplete"] == 0
    categories = {row["category"] for row in manifest["commands"]}
    assert categories >= {"api", "git", "docker", "contest"}


def test_manifest_command_rows_are_complete() -> None:
    for row in integration_coverage_manifest()["commands"]:
        assert row["complete"] is True
        assert row["ok_checks"]
        if not row["fail_exempt"]:
            assert row["fail_checks"]


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
    assert data["summary"] == integration_coverage_summary()


def test_run_unit_script_runs_integration_coverage_gate() -> None:
    text = (ROOT / "scripts" / "docker" / "run-unit.sh").read_text(encoding="utf-8")
    assert "check_integration_coverage.py" in text


def test_smoke_runs_integration_coverage_gate() -> None:
    smoke = (ROOT / "scripts" / "test" / "smoke.sh").read_text(encoding="utf-8")
    assert "check_integration_coverage.py" in smoke
