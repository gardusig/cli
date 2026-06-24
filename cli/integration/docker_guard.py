"""Guard integration fixtures so they only run inside the Docker test harness."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from cli.utils.config import project_root, tags_dir_path


def in_docker_integration() -> bool:
    """True when running under scripts/test/unit.sh or scripts/test/integration.sh."""
    return os.environ.get("CLI_DOCKER_INTEGRATION") == "1"


def require_docker_integration(*, context: str = "integration") -> None:
    """Fail fast when integration fixtures run on the host checkout."""
    if in_docker_integration():
        return
    raise RuntimeError(
        f"{context} must run inside the Docker integration image, not on the host. "
        "Use ./scripts/test/unit.sh or ./scripts/test/integration.sh."
    )


def _reject_tags_dir_scratch(path: Path) -> None:
    """Never create disposable git fixtures under iCloud git-tags."""
    try:
        tags_root = tags_dir_path().resolve()
    except Exception:
        return
    resolved = path.resolve()
    if resolved == tags_root or tags_root in resolved.parents:
        raise RuntimeError(
            f"integration scratch must not live under backup.tags_dir ({tags_root}); "
            f"got {resolved}"
        )


def integration_scratch_dir(*, require_docker: bool = True) -> Path:
    """Writable scratch root for disposable git repos (container-only by default)."""
    if require_docker:
        require_docker_integration(context="Integration scratch")

    if raw := os.environ.get("CLI_INTEGRATION_SCRATCH"):
        base = Path(raw)
    elif in_docker_integration():
        base = Path("/tmp/integration-scratch")
    else:
        base = project_root() / ".integration-scratch"

    base.mkdir(parents=True, exist_ok=True)
    _reject_tags_dir_scratch(base)
    return base


def integration_temp_dir(prefix: str) -> Path:
    """Create a disposable directory under integration scratch (caller must rmtree)."""
    scratch = integration_scratch_dir()
    return Path(tempfile.mkdtemp(prefix=prefix, dir=scratch))


def cleanup_integration_temp_dir(path: Path) -> None:
    """Remove a temp git fixture and its optional bare origin sibling."""
    shutil.rmtree(path, ignore_errors=True)
    origin = path.parent / f"{path.name}-origin.git"
    shutil.rmtree(origin, ignore_errors=True)
