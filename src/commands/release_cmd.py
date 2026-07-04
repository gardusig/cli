"""Release build command — wrap scripts/release/build.sh."""

from __future__ import annotations

import subprocess
from pathlib import Path

import typer

from src.internal.write.gate import require_write_gate

release_app = typer.Typer(help="Build release artifacts.", no_args_is_help=True)

_ROOT = Path(__file__).resolve().parents[2]


@release_app.command("build")
def release_build_cmd(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip write gate."),
) -> None:
    require_write_gate("release-build", ["repo: local"], yes=yes)
    script = _ROOT / "scripts" / "release" / "build.sh"
    subprocess.run(["bash", str(script)], cwd=_ROOT, check=True)
