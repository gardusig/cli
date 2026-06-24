"""Deprecated alias — use ``cli pypi upload``."""

from __future__ import annotations

from pathlib import Path

import typer

from src.commands.pypi import pypi_build_cmd, pypi_upload_cmd

publish_app = typer.Typer(help="(deprecated) use cli pypi", hidden=True, no_args_is_help=True)


@publish_app.command("pypi")
def publish_pypi_cmd(
    yes: bool = typer.Option(False, "--yes", "-y"),
    build_only: bool = typer.Option(False, "--build-only"),
    testpypi: bool = typer.Option(False, "--testpypi"),
    skip_build: bool = typer.Option(False, "--skip-build"),
    dist_dir: Path | None = typer.Option(None, "--dist-dir"),
) -> None:
    """Deprecated wrapper for ``cli pypi upload`` / ``cli pypi build``."""
    if build_only:
        pypi_build_cmd(version=None, dist_dir=dist_dir)
        return
    pypi_upload_cmd(
        yes=yes,
        version=None,
        build_only=False,
        testpypi=testpypi,
        skip_build=skip_build,
        skip_existing=False,
        dist_dir=dist_dir,
    )
