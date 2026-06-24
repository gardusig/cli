"""Create tag zips via git archive (plain) or password-protected zip (private repos)."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from gardusig_cli.utils.process import run_git


def archive_tag_zip(
    repo_path: Path,
    tag: str,
    output: Path,
    *,
    encrypted: bool,
    password: str | None = None,
) -> Path:
    """Archive a git tag to ``output`` (plain zip or AES zip when ``encrypted``)."""
    repo_path = repo_path.resolve()
    run_git(["rev-parse", "-q", "--verify", f"refs/tags/{tag}"], cwd=repo_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    if not encrypted:
        run_git(
            ["archive", "--format=zip", f"--output={output}", tag],
            cwd=repo_path,
        )
        return output

    if not password:
        raise RuntimeError(
            "BACKUP_ZIP_PASSWORD is not set. Export a zip encryption password "
            "for encrypted backup repositories."
        )

    if output.is_file():
        output.unlink()

    with tempfile.TemporaryDirectory(prefix="cli-backup-") as tmp:
        tmp_path = Path(tmp)
        archive = subprocess.run(
            ["git", "archive", tag],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["tar", "-x", "-C", str(tmp_path)],
            input=archive.stdout,
            check=True,
        )
        result = subprocess.run(
            ["zip", "-er", "-P", password, str(output), "."],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            msg = (result.stderr or result.stdout or "zip failed").strip()
            raise RuntimeError(f"encrypted zip failed: {msg}")

    return output
