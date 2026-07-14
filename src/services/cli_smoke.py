"""Read-only integration smoke for an installed ``cli`` binary."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path

from src.utils.config import default_config_dir, project_root


class SmokeError(RuntimeError):
    pass


def _run(argv: Sequence[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def require_cli() -> str:
    cli = shutil.which("cli")
    if not cli:
        raise SmokeError("cli binary not found on PATH")
    return cli


def setup_config(
    *,
    config_dir: Path | None = None,
    workspace: Path | None = None,
) -> dict[str, str]:
    env = dict(os.environ)
    env.setdefault("CLI_PROFILE", "test")
    base = config_dir
    if base is None and env.get("CLI_CONFIG_DIR", "").strip():
        base = Path(env["CLI_CONFIG_DIR"]).expanduser()
    if base is None and workspace is not None:
        candidate = workspace / "config"
        if candidate.is_dir():
            base = candidate
    if base is None:
        for candidate in (
            project_root() / "tests" / "fixtures" / "config",
            project_root() / "config",
        ):
            if candidate.is_dir():
                base = candidate
                break
    if base is None:
        base = default_config_dir()
    env["CLI_CONFIG_DIR"] = str(base.expanduser())
    if not Path(env["CLI_CONFIG_DIR"]).is_dir():
        raise SmokeError(f"CLI_CONFIG_DIR does not exist: {env['CLI_CONFIG_DIR']}")
    return env


def assert_fails(desc: str, argv: Sequence[str], *, env: dict[str, str] | None = None) -> None:
    result = _run(argv, env=env)
    if result.returncode == 0:
        raise SmokeError(f"expected failure: {desc}")


def assert_output_contains(
    desc: str,
    needle: str,
    argv: Sequence[str],
    *,
    env: dict[str, str] | None = None,
) -> None:
    result = _run(argv, env=env)
    if result.returncode != 0:
        raise SmokeError(f"command failed for {desc}: {result.stderr or result.stdout}")
    if needle not in result.stdout:
        raise SmokeError(
            f"expected output to contain {needle!r} for: {desc}\n{result.stdout}"
        )


def prepare_git_repo() -> tuple[Path, dict[str, str]]:
    root = Path(tempfile.mkdtemp(prefix="cli-smoke-git-"))
    env = {"CLI_GIT_ROOT": str(root)}

    def git(*args: str) -> None:
        proc = _run(["git", "-C", str(root), *args], env=env)
        if proc.returncode != 0:
            raise SmokeError(proc.stderr or proc.stdout or f"git {' '.join(args)} failed")

    git("init", "-q", "-b", "main")
    git("config", "user.email", "smoke@test")
    git("config", "user.name", "Smoke")
    (root / "README.md").write_text("init\n", encoding="utf-8")
    git("add", "README.md")
    git("commit", "-q", "-m", "init")
    git("checkout", "-q", "-b", "feature")
    (root / "README.md").write_text("init\nfeature\n", encoding="utf-8")
    git("commit", "-q", "-am", "feature work")
    git("checkout", "-q", "main")
    return root, env


def cleanup_git_repo(root: Path | None) -> None:
    if root is not None and root.is_dir():
        shutil.rmtree(root, ignore_errors=True)


def run_cli_help(cli: str, env: dict[str, str]) -> None:
    for argv in (
        [cli, "--help"],
        [cli, "--version"],
        [cli, "languages", "list"],
        [cli, "git", "--help"],
        [cli, "gh", "--help"],
    ):
        proc = _run(argv, env=env)
        if proc.returncode != 0:
            raise SmokeError(proc.stderr or proc.stdout or f"failed: {' '.join(argv)}")


def run_readonly_git(cli: str, env: dict[str, str]) -> None:
    for argv in (
        [cli, "git", "branch", "current"],
        [cli, "git", "branch", "list"],
        [cli, "git", "log", "oneline", "--base", "main", "--head", "feature"],
        [cli, "git", "diff", "stat", "--base", "main", "--head", "feature"],
        [cli, "git", "rev-list", "count", "--base", "main", "--head", "feature"],
    ):
        proc = _run(argv, env=env)
        if proc.returncode != 0:
            raise SmokeError(proc.stderr or proc.stdout or f"failed: {' '.join(argv)}")


def run_readonly_gh(cli: str, env: dict[str, str]) -> None:
    assert_output_contains("gh policy list", "pr-merge", [cli, "gh", "policy", "list"], env=env)
    assert_fails("gh issue close blocked", [cli, "gh", "issue", "close", "1", "--yes"], env=env)


def run_all(
    *,
    config_dir: Path | None = None,
    workspace: Path | None = None,
    on_progress: Callable[[str], None] | None = None,
) -> None:
    """Run the full read-only smoke suite (raises :class:`SmokeError` on failure)."""
    log = on_progress or (lambda _msg: None)
    cli = require_cli()
    env = setup_config(config_dir=config_dir, workspace=workspace)
    git_root: Path | None = None
    try:
        log("cli help")
        run_cli_help(cli, env)
        log("git fixture")
        git_root, git_env = prepare_git_repo()
        env = {**env, **git_env}
        log("readonly git")
        run_readonly_git(cli, env)
        log("readonly gh")
        run_readonly_gh(cli, env)
    finally:
        cleanup_git_repo(git_root)
    log("integration smoke passed")


def main() -> None:
    try:
        run_all(config_dir=Path(os.environ["CLI_CONFIG_DIR"]) if os.environ.get("CLI_CONFIG_DIR") else None)
    except SmokeError as exc:
        raise SystemExit(str(exc)) from exc
    print("integration smoke passed")


if __name__ == "__main__":
    main()
