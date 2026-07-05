"""Docker execution for contest validation with resource limits."""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from src.services.docker_runtime import ensure_docker, run_docker


class RunStatus(str, Enum):
    OK = "ok"
    TLE = "tle"
    RUNTIME_ERROR = "runtime_error"
    COMPILE_ERROR = "compile_error"


TIMEOUT_EXIT_CODE = 124


@dataclass(frozen=True)
class RunOutcome:
    status: RunStatus
    seconds: float
    stdout: str
    stderr: str
    exit_code: int


@dataclass(frozen=True)
class ContestDockerConfig:
    image: str
    timeout: float
    memory_mb: int
    cxx_std: str = "c++17"


def ensure_contest_image(image: str) -> None:
    ensure_docker()
    result = run_docker(["image", "inspect", image], check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"contest image not found: {image}\n"
            f"Build with the central github-pipelines contest Dockerfile"
        )


def compile_fast_solution(
    workspace: Path,
    *,
    config: ContestDockerConfig,
    source_name: str = "solution.cpp",
    binary_name: str = "solution",
) -> RunOutcome:
    """Compile C++ solution inside a container; binary written to workspace."""
    source = workspace / source_name
    binary = workspace / binary_name
    inner = (
        f"g++ -std={config.cxx_std} -O2 -Wall "
        f"/work/{source_name} -o /work/{binary_name}"
    )
    return _run_docker_shell(workspace, inner, config=config, capture_stdout=False)


def run_brute(
    workspace: Path,
    input_name: str,
    output_name: str,
    *,
    config: ContestDockerConfig,
    brute_name: str = "brute.py",
) -> RunOutcome:
    timeout_s = int(config.timeout) if config.timeout == int(config.timeout) else config.timeout
    inner = (
        f"timeout {timeout_s}s python3 /work/{brute_name} "
        f"< /work/{input_name} > /work/{output_name} 2>/work/brute.err"
    )
    outcome = _run_docker_shell(workspace, inner, config=config, capture_stdout=False)
    err_path = workspace / "brute.err"
    stderr = err_path.read_text(encoding="utf-8") if err_path.exists() else outcome.stderr
    stdout = (workspace / output_name).read_text(encoding="utf-8") if (workspace / output_name).exists() else ""
    return _classify_outcome(outcome.exit_code, outcome.seconds, stdout, stderr)


def run_fast(
    workspace: Path,
    input_name: str,
    output_name: str,
    *,
    config: ContestDockerConfig,
    binary_name: str = "solution",
) -> RunOutcome:
    timeout_s = int(config.timeout) if config.timeout == int(config.timeout) else config.timeout
    inner = (
        f"timeout {timeout_s}s /work/{binary_name} "
        f"< /work/{input_name} > /work/{output_name} 2>/work/fast.err"
    )
    outcome = _run_docker_shell(workspace, inner, config=config, capture_stdout=False)
    err_path = workspace / "fast.err"
    stderr = err_path.read_text(encoding="utf-8") if err_path.exists() else outcome.stderr
    stdout = (workspace / output_name).read_text(encoding="utf-8") if (workspace / output_name).exists() else ""
    return _classify_outcome(outcome.exit_code, outcome.seconds, stdout, stderr)


def _classify_outcome(exit_code: int, seconds: float, stdout: str, stderr: str) -> RunOutcome:
    if exit_code == 0:
        return RunOutcome(RunStatus.OK, seconds, stdout, stderr, exit_code)
    if exit_code == TIMEOUT_EXIT_CODE:
        return RunOutcome(RunStatus.TLE, seconds, stdout, stderr, exit_code)
    return RunOutcome(RunStatus.RUNTIME_ERROR, seconds, stdout, stderr, exit_code)


def _docker_volume_source(workspace: Path) -> Path:
    """Map in-container scratch paths to host paths for nested docker runs."""
    host_root = os.environ.get("CLI_CONTEST_WORKSPACE_HOST_ROOT")
    integration_root = os.environ.get("CLI_CONTEST_WORKSPACE_ROOT")
    if host_root and integration_root:
        try:
            rel = workspace.resolve().relative_to(Path(integration_root).resolve())
        except ValueError:
            return workspace.resolve()
        return Path(host_root) / rel
    return workspace.resolve()


def _run_docker_shell(
    workspace: Path,
    inner_script: str,
    *,
    config: ContestDockerConfig,
    capture_stdout: bool,
) -> RunOutcome:
    ensure_docker()
    memory = f"{config.memory_mb}m"
    host_timeout = config.timeout + 5.0
    cmd = [
        "docker",
        "run",
        "--rm",
        f"--memory={memory}",
        f"--memory-swap={memory}",
        "-v",
        f"{_docker_volume_source(workspace)}:/work:rw",
        "-w",
        "/work",
        config.image,
        "bash",
        "-lc",
        inner_script,
    ]
    start = time.monotonic()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=host_timeout,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - start
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
        return RunOutcome(RunStatus.TLE, elapsed, "", stderr, TIMEOUT_EXIT_CODE)

    elapsed = time.monotonic() - start
    exit_code = result.returncode
    stderr = result.stderr.strip()
    stdout = result.stdout if capture_stdout else ""

    if exit_code != 0 and "g++" in inner_script and "error:" in stderr.lower():
        return RunOutcome(RunStatus.COMPILE_ERROR, elapsed, stdout, stderr, exit_code)

    if exit_code == TIMEOUT_EXIT_CODE:
        return RunOutcome(RunStatus.TLE, elapsed, stdout, stderr, exit_code)
    if exit_code != 0:
        return RunOutcome(RunStatus.RUNTIME_ERROR, elapsed, stdout, stderr, exit_code)
    return RunOutcome(RunStatus.OK, elapsed, stdout, stderr, exit_code)


def classify_compile(outcome: RunOutcome) -> RunOutcome:
    if outcome.exit_code != 0:
        return RunOutcome(
            RunStatus.COMPILE_ERROR,
            outcome.seconds,
            outcome.stdout,
            outcome.stderr,
            outcome.exit_code,
        )
    return outcome
