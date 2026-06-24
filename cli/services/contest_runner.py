"""Two-tier contest validation orchestration."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from cli.services.contest_docker import (
    ContestDockerConfig,
    RunOutcome,
    RunStatus,
    classify_compile,
    compile_fast_solution,
    ensure_contest_image,
    run_brute,
    run_fast,
)
from cli.services.contest_serde import compare_text, unified_diff
from cli.utils.config import load_yaml, project_root


TierName = Literal["small", "large"]


@dataclass(frozen=True)
class ContestPaths:
    fast: Path
    brute: Path
    generator: Path


@dataclass(frozen=True)
class ContestValidateOptions:
    paths: ContestPaths
    timeout: float = 10.0
    memory_mb: int = 256
    image: str = "cli-contest:runner"
    cxx_std: str = "c++17"


@dataclass(frozen=True)
class TierRunResult:
    tier: TierName
    brute: RunOutcome
    fast: RunOutcome
    outputs_match: bool | None = None


@dataclass
class ContestValidateResult:
    passed: bool
    small: TierRunResult | None = None
    large: TierRunResult | None = None
    warnings: list[str] = field(default_factory=list)
    small_diff: str | None = None
    error: str | None = None


def contest_defaults() -> dict:
    path = project_root() / "config" / "contest" / "defaults.yaml"
    return load_yaml(path)


def load_contest_config(config_path: Path) -> dict:
    return load_yaml(config_path)


def resolve_options(
    *,
    fast: Path | None,
    brute: Path | None,
    generator: Path | None,
    config: Path | None,
    timeout: float | None,
    memory_mb: int | None,
    image: str | None,
) -> ContestValidateOptions:
    defaults = contest_defaults()
    cfg: dict = {}
    if config is not None:
        cfg = load_contest_config(config)

    def pick(key: str, cli: object, default: object) -> object:
        if cli is not None:
            return cli
        if key in cfg and cfg[key] is not None:
            return cfg[key]
        return defaults.get(key, default)

    fast_val = pick("fast", fast, None)
    brute_val = pick("brute", brute, None)
    generator_val = pick("generator", generator, None)

    def require_path(label: str, value: object) -> Path:
        if value is None or (isinstance(value, str) and not str(value).strip()):
            raise ValueError(f"missing required path: {label}")
        return Path(value)

    fast_path = require_path("fast", fast_val)
    brute_path = require_path("brute", brute_val)
    generator_path = require_path("generator", generator_val)

    for label, path in [("fast", fast_path), ("brute", brute_path), ("generator", generator_path)]:
        if not str(path) or str(path) == ".":
            raise ValueError(f"missing required path: {label}")
        if not path.exists():
            raise FileNotFoundError(f"{label} not found: {path}")

    return ContestValidateOptions(
        paths=ContestPaths(
            fast=fast_path.resolve(),
            brute=brute_path.resolve(),
            generator=generator_path.resolve(),
        ),
        timeout=float(pick("timeout", timeout, 10.0)),
        memory_mb=int(pick("memory_mb", memory_mb, 256)),
        image=str(pick("image", image, "cli-contest:runner")),
        cxx_std=str(pick("cxx_std", None, "c++17")),
    )


def _docker_config(options: ContestValidateOptions) -> ContestDockerConfig:
    return ContestDockerConfig(
        image=options.image,
        timeout=options.timeout,
        memory_mb=options.memory_mb,
        cxx_std=options.cxx_std,
    )


def _generate_tier(generator: Path, tier: TierName, dest: Path, *, gen_timeout: float = 30.0) -> None:
    result = subprocess.run(
        [sys.executable, str(generator), tier],
        capture_output=True,
        text=True,
        check=False,
        timeout=gen_timeout,
        cwd=str(generator.parent),
    )
    if result.returncode != 0:
        msg = (result.stderr or result.stdout or f"generator failed for tier {tier}").strip()
        raise RuntimeError(msg)
    text = result.stdout
    if not text.strip():
        raise RuntimeError(f"generator produced empty output for tier: {tier}")
    dest.write_text(text, encoding="utf-8")


def _setup_workspace(options: ContestValidateOptions, workspace: Path) -> None:
    shutil.copy2(options.paths.fast, workspace / "solution.cpp")
    shutil.copy2(options.paths.brute, workspace / "brute.py")
    _generate_tier(options.paths.generator, "small", workspace / "small.txt")
    _generate_tier(options.paths.generator, "large", workspace / "large.txt")


def _run_tier_parallel(
    workspace: Path,
    tier: TierName,
    *,
    config: ContestDockerConfig,
) -> TierRunResult:
    input_name = f"{tier}.txt"
    brute_out = f"brute_{tier}.out"
    fast_out = f"fast_{tier}.out"

    with ThreadPoolExecutor(max_workers=2) as pool:
        brute_future = pool.submit(
            run_brute, workspace, input_name, brute_out, config=config
        )
        fast_future = pool.submit(
            run_fast, workspace, input_name, fast_out, config=config
        )
        brute = brute_future.result()
        fast = fast_future.result()

    outputs_match: bool | None = None
    if tier == "small" and brute.status == RunStatus.OK and fast.status == RunStatus.OK:
        brute_text = brute.stdout
        if not brute_text and (workspace / brute_out).exists():
            brute_text = (workspace / brute_out).read_text(encoding="utf-8")
        fast_text = fast.stdout
        if not fast_text and (workspace / fast_out).exists():
            fast_text = (workspace / fast_out).read_text(encoding="utf-8")
        outputs_match = compare_text(brute_text, fast_text)

    return TierRunResult(tier=tier, brute=brute, fast=fast, outputs_match=outputs_match)


def _contest_workspace() -> tempfile.TemporaryDirectory[str]:
    root = os.environ.get("CLI_CONTEST_WORKSPACE_ROOT")
    if root:
        base = Path(root)
        base.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(prefix="cli-contest-", dir=base)
    return tempfile.TemporaryDirectory(prefix="cli-contest-")


def validate_contest(options: ContestValidateOptions) -> ContestValidateResult:
    config = _docker_config(options)
    ensure_contest_image(config.image)

    with _contest_workspace() as tmp:
        workspace = Path(tmp)
        try:
            _setup_workspace(options, workspace)
        except (RuntimeError, OSError) as exc:
            return ContestValidateResult(passed=False, error=str(exc))

        compile_out = classify_compile(
            compile_fast_solution(workspace, config=config)
        )
        if compile_out.status == RunStatus.COMPILE_ERROR:
            return ContestValidateResult(
                passed=False,
                error=f"C++ compile failed:\n{compile_out.stderr}",
            )

        small = _run_tier_parallel(workspace, "small", config=config)

        if small.brute.status != RunStatus.OK:
            return ContestValidateResult(
                passed=False,
                small=small,
                error=f"brute failed on small tier: {small.brute.status.value}",
            )
        if small.fast.status != RunStatus.OK:
            return ContestValidateResult(
                passed=False,
                small=small,
                error=f"fast failed on small tier: {small.fast.status.value}",
            )
        if not small.outputs_match:
            brute_text = small.brute.stdout
            fast_text = small.fast.stdout
            if not brute_text and (workspace / "brute_small.out").exists():
                brute_text = (workspace / "brute_small.out").read_text(encoding="utf-8")
            if not fast_text and (workspace / "fast_small.out").exists():
                fast_text = (workspace / "fast_small.out").read_text(encoding="utf-8")
            return ContestValidateResult(
                passed=False,
                small=small,
                small_diff=unified_diff(brute_text, fast_text),
                error="small tier outputs differ (brute vs fast)",
            )

        large = _run_tier_parallel(workspace, "large", config=config)
        warnings: list[str] = []

        if large.fast.status != RunStatus.OK:
            return ContestValidateResult(
                passed=False,
                small=small,
                large=large,
                error=f"fast failed on large tier: {large.fast.status.value}",
            )

        if large.brute.status == RunStatus.OK:
            warnings.append(
                "brute finished on large input — stress tier may not be heavy enough"
            )

        return ContestValidateResult(
            passed=True,
            small=small,
            large=large,
            warnings=warnings,
        )
