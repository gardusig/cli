"""Integration smoke — installed cli binary + disposable git repo."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.constants import ROOT

SMOKE = ROOT / "scripts" / "pull-request" / "integration-smoke.sh"


def test_integration_smoke_script_exists() -> None:
    assert SMOKE.is_file()


@pytest.mark.integration
def test_integration_smoke_runs() -> None:
    env = dict(os.environ)
    env.setdefault("CLI_CONFIG_DIR", str(ROOT / "config"))
    env.setdefault("CLI_PROFILE", "test")
    result = subprocess.run(["bash", str(SMOKE)], cwd=ROOT, env=env, check=False)
    assert result.returncode == 0, "integration-smoke.sh failed"
