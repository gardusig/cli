"""Release build command."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

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
from src.utils.config import project_root

release_app = typer.Typer(help="Build release artifacts.", no_args_is_help=True)


@release_app.command("build")
def release_build_cmd(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip write gate."),
) -> None:
    require_write_gate("release-build", ["repo: local"], yes=yes)
    root = project_root()
    try:
        artifacts = build_distributions(root)
        typer.echo(f"Built: {', '.join(path.name for path in artifacts)}")
    except PyPiPublishError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


@release_app.command("main")
def release_main_cmd(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip write gate."),
    version: str | None = typer.Option(None, "--version", help="Release version (defaults to pyproject)."),
) -> None:
    """Tag main, publish gardusig-cli to PyPI, and push the release tag."""
    root = project_root()
    try:
        release_version = resolve_release_version(version, root=root) or read_project_version(root)
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
        _ensure_release_tag(tag, root=root)
        artifacts = build_distributions(root, version=release_version)
        uploaded = publish_distributions(
            artifacts,
            token=resolve_pypi_token(),
            repository_url=DEFAULT_REPOSITORY_URL,
        )
        verify_package_version_on_index(PACKAGE_NAME, release_version)
        typer.echo(f"Released {PACKAGE_NAME}=={release_version}: {', '.join(uploaded)}")
    except PyPiPublishError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


def _ensure_release_tag(tag: str, *, root: Path) -> None:
    tag_env = {
        **os.environ,
        "GIT_AUTHOR_NAME": os.environ.get("GIT_AUTHOR_NAME", "gardusig-cli-release"),
        "GIT_AUTHOR_EMAIL": os.environ.get("GIT_AUTHOR_EMAIL", "gardusig@users.noreply.github.com"),
        "GIT_COMMITTER_NAME": os.environ.get("GIT_COMMITTER_NAME", "gardusig-cli-release"),
        "GIT_COMMITTER_EMAIL": os.environ.get("GIT_COMMITTER_EMAIL", "gardusig@users.noreply.github.com"),
    }
    existing = subprocess.run(
        ["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if existing.returncode != 0:
        subprocess.run(
            ["git", "tag", "-a", tag, "-m", tag],
            cwd=root,
            check=True,
            env=tag_env,
        )
    push = subprocess.run(["git", "push", "origin", tag], cwd=root, check=False)
    if push.returncode != 0:
        remote = subprocess.run(
            ["git", "ls-remote", "--tags", "origin", tag],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if not remote.stdout.strip():
            push.check_returncode()
