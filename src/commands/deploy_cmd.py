"""Deploy command — wrap scripts/deploy/deploy.sh."""

from __future__ import annotations

import subprocess
from pathlib import Path

import typer

from src.internal.write.gate import require_write_gate

deploy_app = typer.Typer(help="Deploy (tag main on push).", no_args_is_help=True)

_ROOT = Path(__file__).resolve().parents[2]


@deploy_app.callback(invoke_without_command=True)
def deploy_cmd(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip write gate."),
) -> None:
    require_write_gate("deploy", ["repo: local"], yes=yes)
    script = _ROOT / "scripts" / "deploy" / "deploy.sh"
    subprocess.run(["bash", str(script)], cwd=_ROOT, check=True)
