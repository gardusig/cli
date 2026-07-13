"""`scripts/` and `src/` must remain independent (no cross-links)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.constants import ROOT

PR_SCRIPTS = ROOT / "scripts" / "pull-request"
FORBIDDEN_IN_SCRIPTS = (
    "python3 -m src",
    "python -m src",
)
FORBIDDEN_IN_SRC = (
    "subprocess.run([\"scripts/",
    "subprocess.run(['scripts/",
    "Path(\"scripts/",
    "Path('scripts/",
)
CONSUMER_PREFIX = PR_SCRIPTS / "consumer"
HOST_ONLY_SCRIPTS = {
    PR_SCRIPTS / "host-base-version.sh",
    PR_SCRIPTS / "host-last-published-version.sh",
}
CLI_INVOKE_SCRIPTS = {
    PR_SCRIPTS / "_smoke.sh",
    PR_SCRIPTS / "integration-smoke.sh",
}


def _iter_shell_scripts(base: Path) -> list[Path]:
    return sorted(path for path in base.rglob("*.sh") if path.is_file())


def _code_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(raw)
    return lines


def test_pr_scripts_avoid_cli_package_entrypoints() -> None:
    offenders: list[str] = []
    for path in _iter_shell_scripts(PR_SCRIPTS):
        if path in HOST_ONLY_SCRIPTS or path in CLI_INVOKE_SCRIPTS:
            continue
        if CONSUMER_PREFIX in path.parents or path.parent == CONSUMER_PREFIX:
            continue
        code = "\n".join(_code_lines(path.read_text(encoding="utf-8")))
        for token in FORBIDDEN_IN_SCRIPTS:
            if token in code:
                offenders.append(f"{path.relative_to(ROOT)}: {token}")
        for line in code.splitlines():
            trimmed = line.strip()
            if trimmed.startswith("cli ") or trimmed == "cli":
                offenders.append(f"{path.relative_to(ROOT)}: cli command")
    assert not offenders, "\n".join(offenders)


def test_consumer_scripts_may_invoke_pip_installed_cli() -> None:
    run_sh = PR_SCRIPTS / "consumer" / "run.sh"
    text = run_sh.read_text(encoding="utf-8")
    assert "smoke_run_all" in text
    assert "python3 -m src" not in text


def test_src_does_not_reference_scripts_tree() -> None:
    offenders: list[str] = []
    for path in (ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_IN_SRC:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}: {token}")
    assert not offenders, "\n".join(offenders)


def test_pr_unit_script_enforces_coverage_gate() -> None:
    script = PR_SCRIPTS / "unit-test.sh"
    code = "\n".join(_code_lines(script.read_text(encoding="utf-8")))
    assert "coverage-unit.ini" in code
    assert "--cov-fail-under=80" in code
    assert "python3 -m src" not in code
    assert not any(line.strip().startswith("cli ") for line in code.splitlines())


def test_version_check_uses_host_base_version_not_git() -> None:
    script = PR_SCRIPTS / "version-check.sh"
    code = "\n".join(_code_lines(script.read_text(encoding="utf-8")))
    assert "BASE_VERSION" in code
    assert "git show" not in code
    assert "git fetch" not in code


@pytest.mark.parametrize(
    "relative",
    [
        "Dockerfile",
        ".dockerignore",
        "scripts/_common.sh",
        "scripts/pull-request/unit-test.sh",
    ],
)
def test_allowed_paths_are_not_gitignored(relative: str) -> None:
    path = ROOT / relative
    assert path.is_file(), f"missing {relative}"
    result = pytest.importorskip("subprocess").run(
        ["git", "check-ignore", "-q", str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, f"{relative} is ignored by git"
