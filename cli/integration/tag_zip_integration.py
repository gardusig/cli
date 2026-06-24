"""Multi-step integration checks for git tag and zip commands."""

from __future__ import annotations

import os
import subprocess
import zipfile
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path

from typer.testing import CliRunner

from cli.cli import app
from cli.integration.docker_guard import integration_scratch_dir
from cli.integration.git_mocks import patch_remote_git
from cli.utils.config import default_zip_path
from cli.integration.public_endpoints import (
    _push_cwd,
    dirty_integration_git,
    prepare_git_repo,
    reset_integration_git,
    setup_feature_branch,
)

_CLI_RUNNER = CliRunner()


def _tag_zip_scratch(name: str) -> Path:
    path = integration_scratch_dir() / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def _git(git_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(git_root), *args],
        capture_output=True,
        text=True,
        check=True,
    )


def isolated_tags_env(base: Path) -> dict[str, str]:
    """Config dir with tags_dir under base (avoids real iCloud during tests)."""
    cfg_dir = base / "cli-config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    tags_dir = base / "git-tags"
    tags_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "config.yaml").write_text(
        f"backup:\n  tags_dir: {tags_dir}\n  repositories: []\n",
        encoding="utf-8",
    )
    return {
        "CLI_CONFIG_DIR": str(cfg_dir),
    }


@contextmanager
def _remote_patch(enabled: bool):
    if enabled:
        with patch_remote_git():
            yield
    else:
        yield


def invoke_tag_zip(
    repo_root: Path,
    git_root: Path,
    cli_args: tuple[str, ...],
    *,
    extra_env: dict[str, str] | None = None,
    mock_remote: bool = True,
) -> tuple[int, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    env["CLI_GIT_ROOT"] = str(git_root)
    if extra_env:
        env.update(extra_env)
    with _remote_patch(mock_remote), _push_cwd(repo_root):
        result = _CLI_RUNNER.invoke(app, list(cli_args), env=env)
    return result.exit_code, result.stdout + (result.stderr or "")


def _local_tags(git_root: Path) -> list[str]:
    out = _git(git_root, "tag", "-l").stdout
    return sorted(line.strip() for line in out.splitlines() if line.strip())


def _tag_points_to_head(git_root: Path, tag: str) -> bool:
    head = _git(git_root, "rev-parse", "HEAD").stdout.strip()
    tip = _git(git_root, "rev-parse", f"{tag}^{{}}").stdout.strip()
    return head == tip


def _push_main_to_origin(git_root: Path) -> None:
    _git(git_root, "push", "origin", "main")


def _is_valid_zip(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size == 0:
        return False
    with zipfile.ZipFile(path) as zf:
        return zf.testzip() is None


def check_tag_list_empty(git_root: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    reset_integration_git(git_root)
    scratch = _tag_zip_scratch("tag-list-empty")
    scratch.mkdir(parents=True, exist_ok=True)
    code, output = invoke_tag_zip(
        repo_root,
        git_root,
        ("git", "tag", "list"),
        extra_env=isolated_tags_env(scratch),
    )
    if code != 0:
        return [f"tag list: exit {code}\n{output}"]
    if "Local tags" not in output or "(none)" not in output:
        errors.append(f"tag list empty: unexpected output\n{output}")
    return errors


def check_tag_create_on_main(git_root: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    tag = "integration-create-main"
    reset_integration_git(git_root)
    scratch = _tag_zip_scratch("tag-create-main")
    scratch.mkdir(parents=True, exist_ok=True)
    code, output = invoke_tag_zip(
        repo_root,
        git_root,
        ("git", "tag", tag, "--yes"),
        extra_env=isolated_tags_env(scratch),
    )
    if code != 0:
        return [f"tag create: exit {code}\n{output}"]
    if tag not in output:
        errors.append(f"tag create: missing tag name in output\n{output}")
    if tag not in _local_tags(git_root):
        errors.append(f"tag create: {tag!r} not in local tags")
    if _git(git_root, "branch", "--show-current").stdout.strip() != "main":
        errors.append("tag create: expected to remain on main")
    if not _tag_points_to_head(git_root, tag):
        errors.append("tag create: tag does not point to HEAD")
    return errors


def check_tag_list_after_create(git_root: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    tags = ("integration-list-a", "integration-list-b")
    reset_integration_git(git_root)
    scratch = _tag_zip_scratch("tag-list-after")
    scratch.mkdir(parents=True, exist_ok=True)
    env = isolated_tags_env(scratch)
    for tag in tags:
        code, output = invoke_tag_zip(
            repo_root, git_root, ("git", "tag", tag, "--yes"), extra_env=env
        )
        if code != 0:
            return [f"tag create {tag}: exit {code}\n{output}"]
    code, output = invoke_tag_zip(repo_root, git_root, ("git", "tag", "list"), extra_env=env)
    if code != 0:
        return [f"tag list: exit {code}\n{output}"]
    for tag in tags:
        if tag not in output:
            errors.append(f"tag list: missing {tag!r}\n{output}")
    return errors


def check_tag_refuse_dirty_without_yes(git_root: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    reset_integration_git(git_root)
    dirty_integration_git(git_root)
    scratch = _tag_zip_scratch("tag-refuse-dirty")
    scratch.mkdir(parents=True, exist_ok=True)
    code, output = invoke_tag_zip(
        repo_root,
        git_root,
        ("git", "tag", "integration-dirty-refuse"),
        extra_env=isolated_tags_env(scratch),
    )
    if code == 0:
        errors.append(f"tag refuse dirty: expected failure, got 0\n{output}")
    if "dirty" not in output.lower():
        errors.append(f"tag refuse dirty: missing dirty message\n{output}")
    return errors


def check_tag_refuse_replace_without_yes(git_root: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    tag = "integration-replace-refuse"
    reset_integration_git(git_root)
    scratch = _tag_zip_scratch("tag-replace-refuse")
    scratch.mkdir(parents=True, exist_ok=True)
    env = isolated_tags_env(scratch)
    code, _ = invoke_tag_zip(
        repo_root, git_root, ("git", "tag", tag, "--yes"), extra_env=env
    )
    if code != 0:
        return [f"tag replace setup: failed to create {tag}"]
    code, output = invoke_tag_zip(repo_root, git_root, ("git", "tag", tag), extra_env=env)
    if code == 0:
        errors.append(f"tag replace refuse: expected gate failure\n{output}")
    if "non-interactive" not in output:
        errors.append(f"tag replace refuse: missing write gate message\n{output}")
    return errors


def check_tag_replace_with_yes(git_root: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    tag = "integration-replace-yes"
    reset_integration_git(git_root)
    scratch = _tag_zip_scratch("tag-replace-yes")
    scratch.mkdir(parents=True, exist_ok=True)
    env = isolated_tags_env(scratch)
    invoke_tag_zip(repo_root, git_root, ("git", "tag", tag, "--yes"), extra_env=env)
    _git(git_root, "commit", "--allow-empty", "-m", "advance main")
    _push_main_to_origin(git_root)
    code, output = invoke_tag_zip(repo_root, git_root, ("git", "tag", tag, "--yes"), extra_env=env)
    if code != 0:
        return [f"tag replace: exit {code}\n{output}"]
    if not _tag_points_to_head(git_root, tag):
        errors.append("tag replace: tag should point to new HEAD after replace")
    return errors


def check_tag_push_with_yes(git_root: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    tag = "integration-push-flow"
    reset_integration_git(git_root)
    scratch = _tag_zip_scratch("tag-push-yes")
    scratch.mkdir(parents=True, exist_ok=True)
    env = isolated_tags_env(scratch)
    _git(git_root, "tag", "-a", tag, "-m", tag)
    code, output = invoke_tag_zip(
        repo_root, git_root, ("git", "tag", "push", tag, "--yes"), extra_env=env
    )
    if code != 0:
        return [f"tag push: exit {code}\n{output}"]
    if "pushed" not in output and "skip" not in output:
        errors.append(f"tag push: missing pushed/skip in output\n{output}")
    return errors


def check_tag_push_skip_when_synced(git_root: Path, repo_root: Path) -> list[str]:
    """Real origin: after push, second reconcile skips."""
    errors: list[str] = []
    tag = "integration-push-skip"
    reset_integration_git(git_root)
    scratch = _tag_zip_scratch("tag-push-skip")
    scratch.mkdir(parents=True, exist_ok=True)
    env = isolated_tags_env(scratch)
    _git(git_root, "tag", "-a", tag, "-m", tag)
    _git(git_root, "push", "origin", f"refs/tags/{tag}")
    code, output = invoke_tag_zip(
        repo_root,
        git_root,
        ("git", "tag", "push", tag, "--yes"),
        extra_env=env,
        mock_remote=False,
    )
    if code != 0:
        return [f"tag push skip: exit {code}\n{output}"]
    if "skip" not in output:
        errors.append(f"tag push skip: expected skip message\n{output}")
    return errors


def check_tag_from_feature_aligns_main(git_root: Path, repo_root: Path) -> list[str]:
    """On feature branch, tag --yes syncs main first then tags main tip."""
    errors: list[str] = []
    tag = "integration-from-feature"
    reset_integration_git(git_root)
    setup_feature_branch(git_root, "checked_out")
    scratch = _tag_zip_scratch("tag-from-feature")
    scratch.mkdir(parents=True, exist_ok=True)
    code, output = invoke_tag_zip(
        repo_root,
        git_root,
        ("git", "tag", tag, "--yes"),
        extra_env=isolated_tags_env(scratch),
    )
    if code != 0:
        return [f"tag from feature: exit {code}\n{output}"]
    if _git(git_root, "branch", "--show-current").stdout.strip() != "main":
        errors.append("tag from feature: expected to end on main")
    if tag not in _local_tags(git_root):
        errors.append("tag from feature: tag not created")
    if not _tag_points_to_head(git_root, tag):
        errors.append("tag from feature: tag not on main HEAD")
    return errors


def check_zip_missing_tag(git_root: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    reset_integration_git(git_root)
    scratch = _tag_zip_scratch("zip-missing")
    scratch.mkdir(parents=True, exist_ok=True)
    code, output = invoke_tag_zip(
        repo_root,
        git_root,
        ("git", "zip", "no-such-tag"),
        extra_env=isolated_tags_env(scratch),
    )
    if code == 0:
        errors.append(f"zip missing: expected failure\n{output}")
    if "Tag not found" not in output:
        errors.append(f"zip missing: unexpected message\n{output}")
    return errors


def check_zip_after_tag(git_root: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    tag = "integration-zip-tag"
    reset_integration_git(git_root)
    scratch = _tag_zip_scratch("zip-after-tag")
    scratch.mkdir(parents=True, exist_ok=True)
    env = isolated_tags_env(scratch)
    cfg = Path(env["CLI_CONFIG_DIR"])
    repo_name = git_root.name
    zip_path = default_zip_path(repo_name, tag, config_dir=cfg)

    code, _ = invoke_tag_zip(
        repo_root, git_root, ("git", "tag", tag, "--yes"), extra_env=env
    )
    if code != 0:
        return ["zip after tag: tag create failed"]
    code, output = invoke_tag_zip(repo_root, git_root, ("git", "zip", tag), extra_env=env)
    if code != 0:
        return [f"zip after tag: exit {code}\n{output}"]
    if ".zip" not in output:
        errors.append(f"zip after tag: missing .zip in output\n{output}")
    if not _is_valid_zip(zip_path):
        errors.append(f"zip after tag: invalid or missing archive at {zip_path}")
    return errors


def check_zip_replaces_existing(git_root: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    tag = "integration-zip-replace"
    reset_integration_git(git_root)
    scratch = _tag_zip_scratch("zip-replace")
    scratch.mkdir(parents=True, exist_ok=True)
    env = isolated_tags_env(scratch)
    cfg = Path(env["CLI_CONFIG_DIR"])
    zip_path = default_zip_path(git_root.name, tag, config_dir=cfg)

    invoke_tag_zip(repo_root, git_root, ("git", "tag", tag, "--yes"), extra_env=env)
    invoke_tag_zip(repo_root, git_root, ("git", "zip", tag), extra_env=env)
    first_size = zip_path.stat().st_size
    readme = git_root / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "zip-replace-bump\n", encoding="utf-8")
    _git(git_root, "add", "README.md")
    _git(git_root, "commit", "-m", "bump for zip replace")
    _push_main_to_origin(git_root)
    code, replace_out = invoke_tag_zip(
        repo_root, git_root, ("git", "tag", tag, "--yes"), extra_env=env
    )
    if code != 0:
        return [f"zip replace: tag replace failed\n{replace_out}"]
    code, output = invoke_tag_zip(repo_root, git_root, ("git", "zip", tag), extra_env=env)
    if code != 0:
        return [f"zip replace: exit {code}\n{output}"]
    if not _is_valid_zip(zip_path):
        errors.append("zip replace: archive invalid after second zip")
    if zip_path.stat().st_size == first_size:
        errors.append("zip replace: expected archive content to change after re-tag")
    return errors


def check_zip_custom_output(git_root: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    tag = "integration-zip-custom"
    reset_integration_git(git_root)
    scratch = _tag_zip_scratch("zip-custom")
    scratch.mkdir(parents=True, exist_ok=True)
    custom = scratch / "custom-out.zip"
    env = isolated_tags_env(scratch)
    invoke_tag_zip(repo_root, git_root, ("git", "tag", tag, "--yes"), extra_env=env)
    code, output = invoke_tag_zip(
        repo_root,
        git_root,
        ("git", "zip", tag, "-o", str(custom)),
        extra_env=env,
    )
    if code != 0:
        return [f"zip custom: exit {code}\n{output}"]
    if not _is_valid_zip(custom):
        errors.append(f"zip custom: invalid archive at {custom}")
    return errors


def check_tag_zip_full_workflow(git_root: Path, repo_root: Path) -> list[str]:
    """tag create → list → push → zip in one scenario."""
    errors: list[str] = []
    tag = "integration-full-workflow"
    reset_integration_git(git_root)
    scratch = _tag_zip_scratch("tag-zip-full")
    scratch.mkdir(parents=True, exist_ok=True)
    env = isolated_tags_env(scratch)
    cfg = Path(env["CLI_CONFIG_DIR"])
    zip_path = default_zip_path(git_root.name, tag, config_dir=cfg)

    steps: list[tuple[tuple[str, ...], str]] = [
        (("git", "tag", tag, "--yes"), "tag"),
        (("git", "tag", "list"), "Local tags"),
        (("git", "tag", "push", tag, "--yes"), "push"),
        (("git", "zip", tag), ".zip"),
    ]
    for args, needle in steps:
        code, output = invoke_tag_zip(repo_root, git_root, args, extra_env=env)
        if code != 0:
            errors.append(f"workflow {args}: exit {code}\n{output}")
            return errors
        if needle not in output:
            errors.append(f"workflow {args}: missing {needle!r}\n{output}")
    if tag not in _local_tags(git_root):
        errors.append("workflow: tag missing locally")
    if not _is_valid_zip(zip_path):
        errors.append("workflow: zip archive missing or invalid")
    return errors


TAG_ZIP_CHECKS: tuple[tuple[str, Callable[[Path, Path], list[str]]], ...] = (
    ("tag list empty", check_tag_list_empty),
    ("tag create on main", check_tag_create_on_main),
    ("tag list after create", check_tag_list_after_create),
    ("tag refuse dirty without yes", check_tag_refuse_dirty_without_yes),
    ("tag refuse replace without yes", check_tag_refuse_replace_without_yes),
    ("tag replace with yes", check_tag_replace_with_yes),
    ("tag push with yes", check_tag_push_with_yes),
    ("tag push skip when synced", check_tag_push_skip_when_synced),
    ("tag from feature aligns main", check_tag_from_feature_aligns_main),
    ("zip missing tag", check_zip_missing_tag),
    ("zip after tag", check_zip_after_tag),
    ("zip replaces existing", check_zip_replaces_existing),
    ("zip custom output", check_zip_custom_output),
    ("tag zip full workflow", check_tag_zip_full_workflow),
)


def run_all_tag_zip_checks(repo_root: Path, git_root: Path) -> list[str]:
    from cli.integration.docker_guard import require_docker_integration

    require_docker_integration(context="run_all_tag_zip_checks")
    errors: list[str] = []
    for label, check in TAG_ZIP_CHECKS:
        scenario_errors = check(git_root, repo_root)
        for msg in scenario_errors:
            errors.append(f"{label}: {msg}")
        reset_integration_git(git_root)
    return errors


def prepare_tag_zip_git(path: Path) -> None:
    prepare_git_repo(path)
