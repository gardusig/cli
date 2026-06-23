"""Publish workflows (PyPI)."""

from __future__ import annotations

from pathlib import Path

import typer

from cli.internal.write.gate import require_write_gate
from cli.services.pypi_publish import (
    DEFAULT_REPOSITORY_URL,
    TEST_REPOSITORY_URL,
    PyPiPublishError,
    build_distributions,
    publish_distributions,
    resolve_pypi_token,
)
from cli.utils.config import project_root

publish_app = typer.Typer(help="Publish packages (PyPI).", no_args_is_help=True)


@publish_app.command("pypi")
def publish_pypi_cmd(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
    build_only: bool = typer.Option(False, "--build-only", help="Build dist/ only; no upload."),
    testpypi: bool = typer.Option(False, "--testpypi", help="Upload to TestPyPI."),
    skip_build: bool = typer.Option(False, "--skip-build", help="Upload existing dist/ only."),
    dist_dir: Path | None = typer.Option(None, "--dist-dir", help="Output dir for build (default: dist/)."),
) -> None:
    """Build sdist/wheel and upload to PyPI using PYPI_API_TOKEN."""
    root = project_root()

    try:
        if build_only:
            artifacts = build_distributions(root, output_dir=dist_dir)
            typer.echo(f"Built: {', '.join(path.name for path in artifacts)}")
            return

        token = resolve_pypi_token()
        repo_url = TEST_REPOSITORY_URL if testpypi else DEFAULT_REPOSITORY_URL
        target = "TestPyPI" if testpypi else "PyPI"

        require_write_gate(
            "pypi-publish",
            [f"project: gardusig-cli", f"target: {target}"],
            question=f"Publish gardusig-cli to {target}?",
            yes=yes,
        )

        if skip_build:
            out = (dist_dir or root / "dist").resolve()
            artifacts = sorted(out.glob("*.whl")) + sorted(out.glob("*.tar.gz"))
            if not artifacts:
                raise typer.BadParameter(f"no artifacts in {out} (run without --skip-build)")
        else:
            artifacts = build_distributions(root, output_dir=dist_dir)

        uploaded = publish_distributions(artifacts, token=token, repository_url=repo_url)
        typer.echo(f"Published to {target}: {', '.join(uploaded)}")
    except PyPiPublishError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
