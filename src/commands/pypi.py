"""PyPI build and upload (gardusig-cli)."""

from __future__ import annotations

from pathlib import Path

import typer

from src.internal.write.gate import require_write_gate
from src.services.pypi_publish import (
    DEFAULT_REPOSITORY_URL,
    PACKAGE_NAME,
    TEST_REPOSITORY_URL,
    PyPiPublishError,
    assert_version_increased_vs_ref,
    assert_version_increased_vs_version,
    build_distributions,
    publish_distributions,
    read_project_version,
    resolve_pypi_token,
    resolve_release_version,
    resolve_testpypi_token,
    verify_package_version_on_index,
)
from src.services.tag_policy import resolve_tag_policy, suggest_next_tag
from src.services.git_shortcuts import GitShortcuts
from src.utils.config import project_root

pypi_app = typer.Typer(help="Build and upload gardusig-cli to PyPI.", no_args_is_help=True)
version_app = typer.Typer(help="Package version checks.", no_args_is_help=True)
pypi_app.add_typer(version_app, name="version")


@version_app.command("check")
def pypi_version_check_cmd(
    base: str = typer.Option(
        "origin/main",
        "--base",
        help="Git ref to compare against (must contain pyproject.toml).",
    ),
    base_version: str = typer.Option(
        "",
        "--base-version",
        help="Explicit base version when git refs are unavailable (e.g. Docker CI).",
    ),
) -> None:
    """Fail unless working-tree version is strictly greater than *base* (PR gate)."""
    root = project_root()
    try:
        if base_version.strip():
            head_v = assert_version_increased_vs_version(base_version, root=root)
            typer.echo(f"version ok: {head_v} > {base_version.strip()}")
        else:
            head_v = assert_version_increased_vs_ref(base, root=root)
            typer.echo(f"version ok: {head_v} > {base}")
    except PyPiPublishError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


@version_app.command("suggest")
def pypi_version_suggest_cmd() -> None:
    """Print suggested next package version (patch bump from pyproject.toml)."""
    from src.services.tag_policy import bump_semver

    root = project_root()
    try:
        current = read_project_version(root)
        typer.echo(bump_semver(current, level="patch"))
    except PyPiPublishError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


@version_app.command("tag-suggest")
def pypi_tag_suggest_cmd() -> None:
    """Print suggested next git tag for the current repo (uses config/tag.yaml)."""
    root = project_root()
    try:
        svc = GitShortcuts(top=str(root))
        policy = resolve_tag_policy(root, svc.all_tag_names())
        suggested = suggest_next_tag(svc.all_tag_names(), policy, repo_root=root)
        typer.echo(suggested)
    except PyPiPublishError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


@pypi_app.command("build")
def pypi_build_cmd(
    version: str | None = typer.Option(
        None,
        "--version",
        help="Release version (overrides pyproject.toml; also CLI_RELEASE_VERSION).",
    ),
    dist_dir: Path | None = typer.Option(None, "--dist-dir", help="Output dir (default: dist/)."),
) -> None:
    """Build sdist + wheel into dist/."""
    root = project_root()
    try:
        artifacts = build_distributions(root, output_dir=dist_dir, version=version)
        typer.echo(f"Built: {', '.join(path.name for path in artifacts)}")
    except PyPiPublishError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


@pypi_app.command("upload")
def pypi_upload_cmd(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive write gate."),
    version: str | None = typer.Option(
        None,
        "--version",
        help="Release version (tag without v, or set CLI_RELEASE_VERSION).",
    ),
    build_only: bool = typer.Option(False, "--build-only", help="Build dist/ only; no upload."),
    testpypi: bool = typer.Option(False, "--testpypi", help="Upload to TestPyPI."),
    skip_build: bool = typer.Option(False, "--skip-build", help="Upload existing dist/ only."),
    skip_existing: bool = typer.Option(
        False,
        "--skip-existing",
        help="Skip files that already exist on the index (TestPyPI re-runs).",
    ),
    dist_dir: Path | None = typer.Option(None, "--dist-dir", help="Output dir for build (default: dist/)."),
) -> None:
    """Build and upload gardusig-cli using PYPI_API_TOKEN."""
    root = project_root()

    try:
        release_version = resolve_release_version(version, root=root)
        if build_only:
            artifacts = build_distributions(
                root,
                output_dir=dist_dir,
                version=release_version,
            )
            typer.echo(f"Built: {', '.join(path.name for path in artifacts)}")
            return

        token = resolve_testpypi_token() if testpypi else resolve_pypi_token()
        repo_url = TEST_REPOSITORY_URL if testpypi else DEFAULT_REPOSITORY_URL
        target = "TestPyPI" if testpypi else "PyPI"
        version_line = release_version or "pyproject.toml"
        require_write_gate(
            "pypi-publish",
            [
                "project: gardusig-cli",
                f"target: {target}",
                f"version: {version_line}",
            ],
            question=f"Publish gardusig-cli {version_line} to {target}?",
            yes=yes,
        )

        if skip_build:
            out = (dist_dir or root / "dist").resolve()
            artifacts = sorted(out.glob("*.whl")) + sorted(out.glob("*.tar.gz"))
            if not artifacts:
                raise typer.BadParameter(f"no artifacts in {out} (run without --skip-build)")
        else:
            artifacts = build_distributions(
                root,
                output_dir=dist_dir,
                version=release_version,
            )

        uploaded = publish_distributions(
            artifacts,
            token=token,
            repository_url=repo_url,
            skip_existing=skip_existing,
        )
        published_version = release_version or read_project_version(root)
        verify_package_version_on_index(
            PACKAGE_NAME,
            published_version,
            testpypi=testpypi,
        )
        typer.echo(f"Published to {target}: {', '.join(uploaded)}")
        typer.echo(f"Verified on {target}: {PACKAGE_NAME}=={published_version}")
    except PyPiPublishError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
