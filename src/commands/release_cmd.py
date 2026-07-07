"""Release build command."""

from __future__ import annotations

from pathlib import Path
import subprocess

import typer

from src.internal.write.gate import require_write_gate
from src.services.pypi_publish import (
    DEFAULT_REPOSITORY_URL,
    PACKAGE_NAME,
    PyPiPublishError,
    build_distributions,
    format_release_tag,
    publish_distributions,
    read_project_version,
    resolve_pypi_token,
    resolve_release_version,
    verify_package_version_on_index,
)

release_app = typer.Typer(help="Build release artifacts.", no_args_is_help=True)

_ROOT = Path(__file__).resolve().parents[2]


@release_app.command("build")
def release_build_cmd(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip write gate."),
) -> None:
    require_write_gate("release-build", ["repo: local"], yes=yes)
    try:
        artifacts = build_distributions(_ROOT)
        typer.echo(f"Built: {', '.join(path.name for path in artifacts)}")
    except PyPiPublishError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


@release_app.command("main")
def release_main_cmd(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip write gate."),
    version: str | None = typer.Option(None, "--version", help="Release version (defaults to pyproject)."),
) -> None:
    """Tag main, publish gardusig-cli to PyPI, and create a GitHub release."""
    try:
        release_version = resolve_release_version(version, root=_ROOT) or read_project_version(_ROOT)
        tag = format_release_tag(release_version)
        require_write_gate(
            "release-main",
            [
                "repo: gardusig/cli",
                f"tag: {tag}",
                f"package: {PACKAGE_NAME}=={release_version}",
            ],
            question=f"Publish {PACKAGE_NAME} {release_version} and create {tag}?",
            yes=yes,
        )
        _ensure_release_tag(tag)
        artifacts = build_distributions(_ROOT, version=release_version)
        uploaded = publish_distributions(
            artifacts,
            token=resolve_pypi_token(),
            repository_url=DEFAULT_REPOSITORY_URL,
        )
        verify_package_version_on_index(PACKAGE_NAME, release_version)
        _ensure_github_release(tag)
        typer.echo(f"Released {PACKAGE_NAME}=={release_version}: {', '.join(uploaded)}")
    except PyPiPublishError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


def _ensure_release_tag(tag: str) -> None:
    existing = subprocess.run(
        ["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"],
        cwd=_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if existing.returncode != 0:
        subprocess.run(["git", "tag", "-a", tag, "-m", tag], cwd=_ROOT, check=True)
    subprocess.run(["git", "push", "origin", tag], cwd=_ROOT, check=True)


def _ensure_github_release(tag: str) -> None:
    view = subprocess.run(
        ["gh", "release", "view", tag],
        cwd=_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if view.returncode == 0:
        return
    subprocess.run(["gh", "release", "create", tag, "--generate-notes"], cwd=_ROOT, check=True)
